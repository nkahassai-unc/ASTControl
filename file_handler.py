import os
import shutil
import time
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

# Configuration
WATCHED_DIR = 'Z:\\oatest\\402'  # Folder to monitor for new files
DEST_BASE_DIR = 'C:\\Users\\Sundisk\\Desktop\\preprocess'  # Main directory to copy files into
DELETE_HOUR = 21  # 24-hour format for "end of the day" cleanup time
STABILITY_CHECK_TIME = 3  # Seconds to wait for the file to stabilize in size

class CustomHandler(FileSystemEventHandler):
    def __init__(self):
        super(CustomHandler, self).__init__()
        self.file_count = 0
        self.current_day = datetime.now().date()

    def is_file_write_complete(self, filepath):
        """Check if the file size remains constant indicating write completion."""
        initial_size = os.path.getsize(filepath)
        time.sleep(STABILITY_CHECK_TIME)
        final_size = os.path.getsize(filepath)
        return initial_size == final_size

    def on_created(self, event):
        """Handle new file creation event."""
        if not event.is_directory:
            print(f"Detected new file: {event.src_path}")
            if self.is_file_write_complete(event.src_path):
                now = datetime.now()
                # Reset file count if it's a new day
                if now.date() != self.current_day:
                    self.current_day = now.date()
                    self.file_count = 0
                self.file_count += 1
                
                new_folder_name = now.strftime('%Y_%m_%d_%H_%M') + f"_{self.file_count}"
                new_folder_path = os.path.join(DEST_BASE_DIR, new_folder_name)
                os.makedirs(new_folder_path, exist_ok=True)
                destination_file_path = os.path.join(new_folder_path, os.path.basename(event.src_path))
                
                # Copy the fully written file
                shutil.copy(event.src_path, destination_file_path)
                print(f"Copied {event.src_path} to {destination_file_path}")
            else:
                print(f"File {event.src_path} is still writing.")

def daily_cleanup():
    """Perform daily cleanup of old files."""
    last_cleanup_date = datetime.now().date() - timedelta(days=1)  # Ensure cleanup runs the first time
    while True:
        now = datetime.now()
        if now.date() > last_cleanup_date and now.hour == DELETE_HOUR and now.minute < 5:
            last_cleanup_date = now.date()
            for folder_name in os.listdir(DEST_BASE_DIR):
                folder_path = os.path.join(DEST_BASE_DIR, folder_name)
                if os.path.isdir(folder_path):
                    try:
                        shutil.rmtree(folder_path)
                        print(f"Deleted folder {folder_path}")
                    except Exception as e:
                        print(f"Error deleting folder {folder_path}: {e}")
            time.sleep(300)  # Wait 5 minutes before checking again
        else:
            time.sleep(60)  # Check every minute otherwise

def main():
    """Main function to start the observer and cleanup thread."""
    event_handler = CustomHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCHED_DIR, recursive=False)
    observer.start()
    
    cleanup_thread = threading.Thread(target=daily_cleanup, args=())
    cleanup_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.stop()
    observer.join()
    cleanup_thread.join()

if __name__ == "__main__":
    main()

# Monitors and copies files from a watched directory to a destination directory

import os
import shutil
import time
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

# Configuration
WATCHED_DIR = 'Q:\\fc_test\\solar_capture'  # Folder to monitor for new files
DEST_BASE_DIR = 'C:\\Users\\Sundisk\\Desktop\\preprocess'  # Main directory to copy files into
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
                
                date_str = now.strftime('%m%d%y')
                time_str = now.strftime('%H%M%S')
                new_folder_name = f"{self.file_count}_{date_str}_{time_str}"
                new_folder_path = os.path.join(DEST_BASE_DIR, new_folder_name)
                os.makedirs(new_folder_path, exist_ok=True)
                destination_file_path = os.path.join(new_folder_path, os.path.basename(event.src_path))
                
                # Copy the fully written file
                try:
                    shutil.copy(event.src_path, destination_file_path)
                    print(f"Copied {event.src_path} to {destination_file_path}")
                    # Delete the original file after copying
                    os.remove(event.src_path)
                    print(f"Deleted original file {event.src_path}")
                except Exception as e:
                    print(f"Error copying or deleting file {event.src_path}: {e}")
            else:
                print(f"File {event.src_path} is still being written.")

def main():
    """Main function to start the observer."""
    event_handler = CustomHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCHED_DIR, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
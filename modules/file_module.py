# File Handling Module
# Monitors and copies files from a watched directory to a destination directory

import os
import shutil
import time
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
BASE_WATCHED_DIR = 'Q:\\fc_test\\solarcaptureii'  # Folder to monitor
DEST_BASE_DIR = 'C:\\Users\\Sundisk\\Desktop\\preprocess'  # Destination
STABILITY_CHECK_TIME = 3  # Seconds to wait to check file stability

class FileHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.file_count = 0
        self.current_day = datetime.now().date()

    def is_file_write_complete(self, filepath):
        initial_size = os.path.getsize(filepath)
        time.sleep(STABILITY_CHECK_TIME)
        final_size = os.path.getsize(filepath)
        return initial_size == final_size

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.avi'):
            print(f"Detected new AVI file: {event.src_path}")
            if self.is_file_write_complete(event.src_path):
                now = datetime.now()
                if now.date() != self.current_day:
                    self.current_day = now.date()
                    self.file_count = 0
                self.file_count += 1

                date_str = now.strftime('%m%d%y')
                time_str = now.strftime('%H%M%S')
                new_folder = f"{self.file_count}_{date_str}_{time_str}"
                new_path = os.path.join(DEST_BASE_DIR, new_folder)
                os.makedirs(new_path, exist_ok=True)

                dest_file = os.path.join(new_path, os.path.basename(event.src_path))
                try:
                    shutil.copy(event.src_path, dest_file)
                    print(f"Copied to {dest_file}")
                    os.remove(event.src_path)
                    print(f"Deleted original file {event.src_path}")
                except Exception as e:
                    print(f"Error handling {event.src_path}: {e}")
            else:
                print(f"File {event.src_path} still writing...")

    @staticmethod
    def get_file_list():
        """Return list of copied files with name, size, and timestamp."""
        file_data = []
        for folder in os.listdir(DEST_BASE_DIR):
            folder_path = os.path.join(DEST_BASE_DIR, folder)
            if os.path.isdir(folder_path):
                for f in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, f)
                    if os.path.isfile(file_path):
                        stats = os.stat(file_path)
                        file_data.append({
                            "name": f,
                            "size": f"{stats.st_size // 1024} KB",
                            "modified": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                        })
        return file_data

def main():
    today_str = datetime.now().strftime('%d%m%y')
    WATCHED_DIR = os.path.join(BASE_WATCHED_DIR, today_str)

    if not os.path.exists(WATCHED_DIR):
        print(f"Directory {WATCHED_DIR} doesn't exist.")
        return

    handler = FileHandler()
    observer = Observer()
    observer.schedule(handler, WATCHED_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()

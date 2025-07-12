# File Handling Module
# Monitors and copies files from a watched directory to a destination directory

import os
import shutil
import time
from datetime import datetime

# Configuration
from utilities.config import FILE_WATCH_DIR, FILE_DEST_DIR, FILE_STATUS

STABILITY_CHECK_TIME = 3  # Seconds to wait to check file stability

class FileHandler:
    def __init__(self):
        self.file_count = 0
        self.current_day = datetime.now().date()

    def is_file_write_complete(self, filepath):
        initial_size = os.path.getsize(filepath)
        time.sleep(STABILITY_CHECK_TIME)
        final_size = os.path.getsize(filepath)
        return initial_size == final_size

    def process_file(self, filepath):
        filename = os.path.basename(filepath)
        FILE_STATUS[filename] = "Detected"

        if not self.is_file_write_complete(filepath):
            FILE_STATUS[filename] = "Failed"
            print(f"[FileHandler] File still writing: {filename}")
            return

        FILE_STATUS[filename] = "Copying"

        now = datetime.now()
        if now.date() != self.current_day:
            self.current_day = now.date()
            self.file_count = 0
        self.file_count += 1

        date_str = now.strftime('%m%d%y')
        time_str = now.strftime('%H%M%S')
        new_folder = f"{self.file_count}_{date_str}_{time_str}"
        new_path = os.path.join(FILE_DEST_DIR, new_folder)
        os.makedirs(new_path, exist_ok=True)

        dest_file = os.path.join(new_path, filename)
        try:
            shutil.copy(filepath, dest_file)
            FILE_STATUS[filename] = "Copied"
            print(f"[FileHandler] Copied: {filename} → {dest_file}")
            os.remove(filepath)
            print(f"[FileHandler] Deleted original: {filename}")
        except Exception as e:
            FILE_STATUS[filename] = "Failed"
            print(f"[FileHandler] Error copying {filename}: {e}")

    def check_directory(self):
        today_str = datetime.now().strftime('%m%d%y')
        watched_today = os.path.join(FILE_WATCH_DIR, today_str)

        if not os.path.exists(watched_today):
            print(f"[FileHandler] Watch directory does not exist: {watched_today}")
            return

        for f in os.listdir(watched_today):
            if f.lower().endswith(".avi"):
                full_path = os.path.join(watched_today, f)
                if f not in FILE_STATUS:
                    self.process_file(full_path)

    @staticmethod
    def get_file_list():
        """Return list of copied files with name, size, and timestamp."""
        file_data = []
        for folder in os.listdir(FILE_DEST_DIR):
            folder_path = os.path.join(FILE_DEST_DIR, folder)
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
    handler = FileHandler()
    try:
        while True:
            handler.check_directory()
            time.sleep(3)
    except KeyboardInterrupt:
        print("[FileHandler] Stopped.")

if __name__ == "__main__":
    main()
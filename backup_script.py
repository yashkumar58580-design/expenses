import shutil
import os
from datetime import datetime

# Rules
DATABASE_FILE = "future_finance.db"
BACKUP_DIR = "backups"

def do_backup():
    # Agar folder nahi hai toh banao
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"📂 Created: {BACKUP_DIR}")

    # Unique name with timestamp
    time_now = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = f"{BACKUP_DIR}/backup_{time_now}.db"

    # Action
    if os.path.exists(DATABASE_FILE):
        shutil.copy2(DATABASE_FILE, destination)
        print(f"✅ Success! Backup saved: {destination}")
    else:
        print("❌ Error: future_finance.db nahi mila!")

if __name__ == "__main__":
    do_backup()

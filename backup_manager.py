"""
Backup Manager for සමාලි Bot
Run this separately for automated backups
"""
import os
import json
import shutil
import datetime
from pathlib import Path

class BackupManager:
    def __init__(self):
        self.backup_dir = "backups"
        self.memory_dir = "memory"
        self.config_files = ["bot.config", "developer_settings.json"]
        
        # Create backup directory
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self):
        """Create a backup of all important data"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Backup memory
            if os.path.exists(self.memory_dir):
                memory_backup = os.path.join(backup_path, "memory")
                shutil.copytree(self.memory_dir, memory_backup)
                print(f"✅ Backed up memory to {memory_backup}")
            
            # Backup config files
            for config_file in self.config_files:
                if os.path.exists(config_file):
                    shutil.copy2(config_file, backup_path)
                    print(f"✅ Backed up {config_file}")
            
            # Create backup info file
            backup_info = {
                "timestamp": timestamp,
                "backup_name": backup_name,
                "files": os.listdir(backup_path),
                "size_mb": self.get_folder_size(backup_path) / (1024*1024)
            }
            
            info_file = os.path.join(backup_path, "backup_info.json")
            with open(info_file, "w", encoding="utf-8") as f:
                json.dump(backup_info, f, indent=2)
            
            print(f"✅ Backup created: {backup_name}")
            return backup_path
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    
    def get_folder_size(self, folder_path):
        """Get folder size in bytes"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size
    
    def list_backups(self):
        """List all available backups"""
        if not os.path.exists(self.backup_dir):
            return []
        
        backups = []
        for item in os.listdir(self.backup_dir):
            backup_path = os.path.join(self.backup_dir, item)
            if os.path.isdir(backup_path):
                info_file = os.path.join(backup_path, "backup_info.json")
                if os.path.exists(info_file):
                    try:
                        with open(info_file, "r", encoding="utf-8") as f:
                            info = json.load(f)
                        backups.append(info)
                    except:
                        pass
        
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)
    
    def restore_backup(self, backup_name):
        """Restore from a backup"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        if not os.path.exists(backup_path):
            print(f"❌ Backup not found: {backup_name}")
            return False
        
        try:
            print(f"🔄 Restoring from backup: {backup_name}")
            
            # Restore memory
            memory_backup = os.path.join(backup_path, "memory")
            if os.path.exists(memory_backup):
                if os.path.exists(self.memory_dir):
                    shutil.rmtree(self.memory_dir)
                shutil.copytree(memory_backup, self.memory_dir)
                print("✅ Memory restored")
            
            # Restore config files
            for config_file in self.config_files:
                backup_file = os.path.join(backup_path, config_file)
                if os.path.exists(backup_file):
                    shutil.copy2(backup_file, config_file)
                    print(f"✅ {config_file} restored")
            
            print("✅ Backup restored successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False

if __name__ == "__main__":
    # Simple backup script
    manager = BackupManager()
    
    print("📦 සමාලි Bot Backup Manager")
    print("1. Create backup")
    print("2. List backups")
    print("3. Restore backup")
    
    choice = input("Select option (1-3): ").strip()
    
    if choice == "1":
        manager.create_backup()
    elif choice == "2":
        backups = manager.list_backups()
        if backups:
            print(f"\n📚 Available backups ({len(backups)}):")
            for backup in backups:
                print(f"• {backup['backup_name']} ({backup['size_mb']:.2f} MB)")
        else:
            print("No backups found")
    elif choice == "3":
        backup_name = input("Enter backup name to restore: ").strip()
        manager.restore_backup(backup_name)
    else:
        print("Invalid choice")

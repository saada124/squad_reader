import os
import shutil
from datetime import datetime
from typing import Tuple, List

def create_load_backup(filepath: str) -> Tuple[str, str]:
    """
    Creates an immediate safety duplicate of the squads file in the same directory.
    Format: <OriginalName>.backup_<YYYYMMDD_HHMMSS>
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Squads file not found: {filepath}")
    
    file_dir = os.path.dirname(os.path.abspath(filepath))
    file_name = os.path.basename(filepath)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_name}.backup_{timestamp}"
    backup_path = os.path.join(file_dir, backup_name)
    
    shutil.copy2(filepath, backup_path)
    msg = f"Created safety backup: {backup_name}"
    return backup_path, msg

def list_folder_backups(filepath: str) -> List[str]:
    """Lists all backup copies existing in the same folder as filepath."""
    if not os.path.exists(filepath):
        return []
    file_dir = os.path.dirname(os.path.abspath(filepath))
    file_name = os.path.basename(filepath)
    prefix = f"{file_name}.backup_"
    
    backups = []
    try:
        for entry in os.listdir(file_dir):
            if entry.startswith(prefix):
                backups.append(os.path.join(file_dir, entry))
    except Exception:
        pass
    return sorted(backups, reverse=True)

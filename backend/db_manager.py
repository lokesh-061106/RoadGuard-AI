import os
import json
import threading
from typing import Dict, List, Any, Optional

class JSONDatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(JSONDatabaseManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_dir: str = None):
        if self._initialized:
            return
        
        if db_dir is None:
            # Default to the folder where this script is located + 'db'
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_dir = os.path.join(base_dir, 'db')
        else:
            self.db_dir = db_dir

        os.makedirs(self.db_dir, exist_ok=True)
        self.locks: Dict[str, threading.Lock] = {}
        self._initialized = True

    def _get_file_lock(self, filename: str) -> threading.Lock:
        with self._lock:
            if filename not in self.locks:
                self.locks[filename] = threading.Lock()
            return self.locks[filename]

    def _get_path(self, filename: str) -> str:
        if not filename.endswith('.json'):
            filename += '.json'
        return os.path.join(self.db_dir, filename)

    def read(self, filename: str, default: Any = None) -> Any:
        file_path = self._get_path(filename)
        lock = self._get_file_lock(filename)

        with lock:
            if not os.path.exists(file_path):
                # Write default structure if file does not exist
                initial_data = default if default is not None else ([] if filename != 'analytics' and filename != 'analytics.json' else {})
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(initial_data, f, indent=2)
                    return initial_data
                except Exception as e:
                    print(f"Error initializing file {file_path}: {e}")
                    return initial_data
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return default if default is not None else ([] if filename != 'analytics' and filename != 'analytics.json' else {})
                    return json.loads(content)
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                return default if default is not None else ([] if filename != 'analytics' and filename != 'analytics.json' else {})

    def write(self, filename: str, data: Any) -> bool:
        file_path = self._get_path(filename)
        lock = self._get_file_lock(filename)

        with lock:
            try:
                # Write to a temp file first then rename it to ensure atomic writes
                temp_path = file_path + '.tmp'
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                # Replace the original file
                if os.path.exists(file_path):
                    os.remove(file_path)
                os.rename(temp_path, file_path)
                return True
            except Exception as e:
                print(f"Error writing to file {file_path}: {e}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                return False

# Export a default instance
db = JSONDatabaseManager()

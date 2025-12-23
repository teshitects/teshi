import os
import time
from typing import Set, Dict, Callable
from threading import Thread, Lock
from pathlib import Path


class FileWatcher:
    """Simple file watcher for detecting file changes"""
    
    def __init__(self, watch_paths: list, callback: Callable[[str, str], None], check_interval: float = 2.0):
        """
        Initialize file watcher
        
        Args:
            watch_paths: List of paths to watch
            callback: Callback function that receives (file_path, event_type) parameters
            check_interval: Check interval in seconds
        """
        self.watch_paths = watch_paths
        self.callback = callback
        self.check_interval = check_interval
        
        self._file_mtimes: Dict[str, float] = {}
        self._watching = False
        self._thread = None
        self._lock = Lock()
        
        # Delay initial scan to avoid blocking startup
        import threading
        threading.Thread(target=self._scan_files, kwargs={'initial_scan': True}, daemon=True).start()
    
    def _scan_files(self, initial_scan: bool = False):
        """Scan all files and record modification times"""
        with self._lock:
            current_files = set()
            
            for watch_path in self.watch_paths:
                if os.path.isfile(watch_path):
                    current_files.add(watch_path)
                elif os.path.isdir(watch_path):
                    for root, dirs, files in os.walk(watch_path):
                        # Skip hidden directories
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        
                        for file in files:
                            if file.endswith('.md'):  # Only monitor Markdown files
                                file_path = os.path.join(root, file)
                                current_files.add(file_path)
            
            # Detect new and modified files
            for file_path in current_files:
                try:
                    mtime = os.path.getmtime(file_path)
                    if file_path not in self._file_mtimes:
                        # New file
                        self._file_mtimes[file_path] = mtime
                        # Only trigger callback if this is not the initial scan
                        if not initial_scan:
                            self._safe_callback(file_path, 'created')
                    elif self._file_mtimes[file_path] != mtime:
                        # File modified
                        self._file_mtimes[file_path] = mtime
                        self._safe_callback(file_path, 'modified')
                except OSError:
                    continue
            
            # Detect deleted files (only on subsequent scans)
            if not initial_scan:
                deleted_files = set(self._file_mtimes.keys()) - current_files
                for file_path in deleted_files:
                    del self._file_mtimes[file_path]
                    self._safe_callback(file_path, 'deleted')
    
    def _safe_callback(self, file_path: str, event_type: str):
        """Safely call callback function"""
        try:
            self.callback(file_path, event_type)
        except Exception as e:
            print(f"Error in file watcher callback: {e}")
    
    def _watch_loop(self):
        """Watch loop"""
        while self._watching:
            try:
                self._scan_files()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Error in file watcher: {e}")
                time.sleep(self.check_interval)
    
    def start(self):
        """Start watching"""
        if self._watching:
            return
        
        self._watching = True
        self._thread = Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop watching"""
        self._watching = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
    
    def is_watching(self) -> bool:
        """Whether currently watching"""
        return self._watching
    
    def add_watch_path(self, path: str):
        """Add watch path"""
        if path not in self.watch_paths:
            self.watch_paths.append(path)
            if self._watching:
                self._scan_files()
    
    def remove_watch_path(self, path: str):
        """Remove watch path"""
        if path in self.watch_paths:
            self.watch_paths.remove(path)
            # Remove files under this path from status
            with self._lock:
                files_to_remove = [
                    file_path for file_path in self._file_mtimes.keys()
                    if file_path.startswith(path)
                ]
                for file_path in files_to_remove:
                    del self._file_mtimes[file_path]
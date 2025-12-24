"""Tree utilities for building hierarchical tree structures from file paths."""
import os
from PySide6.QtGui import QStandardItem, QIcon
from PySide6.QtCore import Qt
from teshi.utils.resource_path import resource_path


class TreeBuilder:
    """Utility class for building tree structures from file paths."""
    
    def __init__(self):
        # Icons will be loaded lazily
        self._folder_icon = None
        self._file_icon = None
        self._unknown_file_icon = None
        
        # Skip directories for project trees
        self.skip_dirs = {'.git', '.teshi', '__pycache__', 'node_modules', '.vscode', '.idea', 'build', 'dist'}
    
    @property
    def folder_icon(self):
        if self._folder_icon is None:
            self._folder_icon = QIcon(resource_path("assets/icons/folder.png"))
        return self._folder_icon
    
    @property
    def file_icon(self):
        if self._file_icon is None:
            self._file_icon = QIcon(resource_path("assets/icons/testcase_normal.png"))
        return self._file_icon
    
    @property
    def unknown_file_icon(self):
        if self._unknown_file_icon is None:
            self._unknown_file_icon = QIcon(resource_path("assets/icons/unknown_file.png"))
        return self._unknown_file_icon
        
    def find_project_root(self, file_path):
        """Find the project root by looking for common project indicators."""
        current_dir = os.path.dirname(file_path)
        
        # Look for project indicators up the directory tree
        project_indicators = ['pyproject.toml', 'setup.py', 'package.json', 'requirements.txt', 'teshi.toml']
        
        while current_dir and current_dir != os.path.dirname(current_dir):  # Stop at filesystem root
            for indicator in project_indicators:
                indicator_path = os.path.join(current_dir, indicator)
                if os.path.exists(indicator_path):
                    return current_dir
            current_dir = os.path.dirname(current_dir)
            
        # If no project indicators found, use the parent of the file's directory
        return os.path.dirname(file_path) if file_path else None
    
    def find_common_root(self, file_paths):
        """Find the common parent directory for multiple file paths."""
        if not file_paths:
            return None
            
        if len(file_paths) == 1:
            return self.find_project_root(file_paths[0])
        
        # Get normalized paths
        normalized_paths = [os.path.normpath(path) for path in file_paths]
        
        # Split paths into parts
        path_parts_list = [path.split(os.sep) for path in normalized_paths]
        
        # Find common prefix
        common_parts = []
        for i in range(min(len(parts) for parts in path_parts_list)):
            first_part = path_parts_list[0][i]
            if all(parts[i] == first_part for parts in path_parts_list):
                common_parts.append(first_part)
            else:
                break
        
        # If no common parts found, use the first file's project root
        if not common_parts:
            return self.find_project_root(file_paths[0])
        
        # Join common parts to get the common root
        common_root = os.sep.join(common_parts)
        
        # If common root is just a drive letter (Windows), use the first file's project root
        if len(common_root) <= 3 and common_root.endswith(':'):
            return self.find_project_root(file_paths[0])
            
        # Check if this common root exists and is a directory
        if os.path.exists(common_root) and os.path.isdir(common_root):
            # Try to find a better project root starting from this common root
            return self.find_project_root_from_base(common_root)
        
        # Fallback to the first file's project root
        return self.find_project_root(file_paths[0])
    
    def find_project_root_from_base(self, base_dir):
        """Find project root starting from a base directory."""
        current_dir = base_dir
        
        # Look for project indicators up the directory tree
        project_indicators = ['pyproject.toml', 'setup.py', 'package.json', 'requirements.txt', 'teshi.toml']
        
        while current_dir and current_dir != os.path.dirname(current_dir):
            for indicator in project_indicators:
                indicator_path = os.path.join(current_dir, indicator)
                if os.path.exists(indicator_path):
                    return current_dir
            current_dir = os.path.dirname(current_dir)
            
        return base_dir
        
    def find_or_create_dir_item(self, parent_item, dir_name, dir_path, model=None):
        """Find existing directory item or create a new one."""
        # Check if this directory already exists under the parent
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child and child.text() == dir_name:
                return child
                
        # Create new directory item
        dir_item = QStandardItem(dir_name)
        dir_item.setEditable(False)
        dir_item.setIcon(self.folder_icon)
        dir_item.setData(dir_path, Qt.UserRole)
        parent_item.appendRow(dir_item)
        return dir_item
        
    def add_file_path_to_tree(self, model, file_path, result_data=None, file_icon=None, project_root=None):
        """Add a file path to the tree with full hierarchy."""
        if not project_root:
            project_root = self.find_project_root(file_path)
            
        if not project_root:
            # Fallback: just add the file directly
            file_name = os.path.basename(file_path)
            display_name = file_name
            
            # Use custom display name if result_data is provided
            if result_data and isinstance(result_data, dict):
                display_name = result_data.get('name_snippet', result_data.get('name', file_name))
                # For tree display, remove HTML tags
                if "<mark>" in display_name:
                    display_name = display_name.replace("<mark>", "").replace("</mark>", "")
                    
            file_item = QStandardItem(display_name)
            file_item.setEditable(False)
            file_item.setIcon(file_icon or self.file_icon)
            file_item.setData(result_data or file_path, Qt.UserRole)
            model.appendRow(file_item)
            return
            
        # Get relative path from project root
        try:
            rel_path = os.path.relpath(file_path, project_root)
        except ValueError:
            # Different drives on Windows, fallback to absolute path
            rel_path = file_path
            
        # Split path components using os.path.normpath to normalize path separators
        rel_path = os.path.normpath(rel_path)
        path_parts = rel_path.split(os.sep)
        
        # Build/create the tree hierarchy
        current_parent = model.invisibleRootItem()
        current_path = project_root
        
        for i, part in enumerate(path_parts):
            current_path = os.path.join(current_path, part)
            
            # Check if this is a file (last part and has file extension)
            if i == len(path_parts) - 1 and os.path.splitext(part)[1]:
                # This is the file - create the result item
                display_name = part
                
                # Use custom display name if result_data is provided
                if result_data and isinstance(result_data, dict):
                    display_name = result_data.get('name_snippet', result_data.get('name', part))
                    # For tree display, remove HTML tags
                    if "<mark>" in display_name:
                        display_name = display_name.replace("<mark>", "").replace("</mark>", "")
                        
                file_item = QStandardItem(display_name)
                file_item.setEditable(False)
                file_item.setIcon(file_icon or self.file_icon)
                file_item.setData(result_data or file_path, Qt.UserRole)
                current_parent.appendRow(file_item)
            else:
                # This is a directory - find or create it
                dir_item = self.find_or_create_dir_item(current_parent, part, current_path, model)
                current_parent = dir_item
                
    def populate_tree_from_directory(self, parent_item, path, lazy_load=True, show_md_files_only=True):
        """Populate tree with directory contents. If lazy_load=True, only load immediate children."""
        try:
            entries = []
            try:
                entries = os.listdir(path)
            except PermissionError:
                return
            
            # Separate directories and files, sort them
            dirs = []
            files = []
            
            for entry in entries:
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    if entry.startswith('.') or entry in self.skip_dirs:
                        continue
                    dirs.append((entry, full_path))
                else:
                    files.append((entry, full_path))
            
            # Sort directories and files separately
            dirs.sort(key=lambda x: x[0].lower())
            files.sort(key=lambda x: x[0].lower())
            
            # Add directories first
            for entry_name, full_path in dirs:
                item = QStandardItem(entry_name)
                item.setEditable(False)
                item.setIcon(self.folder_icon)
                item.setData(full_path, Qt.UserRole)
                
                # Add a dummy child to show expand arrow for lazy loading
                if lazy_load:
                    dummy_item = QStandardItem("Loading...")
                    dummy_item.setEditable(False)
                    item.appendRow(dummy_item)
                
                parent_item.appendRow(item)
            
            # Then add files
            for entry_name, full_path in files:
                # Filter files based on show_md_files_only parameter
                if show_md_files_only and not full_path.lower().endswith(('.md', '.markdown')):
                    continue
                    
                # Choose appropriate icon based on file type
                if full_path.lower().endswith(('.md', '.markdown')):
                    icon = self.file_icon
                else:
                    icon = self.unknown_file_icon
                    
                item = QStandardItem(entry_name)
                item.setEditable(False)
                item.setIcon(icon)
                item.setData(full_path, Qt.UserRole)
                parent_item.appendRow(item)
                
        except PermissionError:
            pass
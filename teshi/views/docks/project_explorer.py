import sys
import os
import shutil
from PySide6.QtWidgets import (
    QApplication, QTreeView, QMenu, QInputDialog, QMessageBox
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide6.QtCore import Qt, Signal, QModelIndex
import platform
import subprocess
from teshi.utils.resource_path import resource_path
from teshi.utils.tree_utils import TreeBuilder


class ProjectExplorer(QTreeView):
    file_open_requested = Signal(str)
    state_changed = Signal()
    def __init__(self, target_dir):
        super().__init__()
        self.setWindowTitle("Project Explorer")
        self.setHeaderHidden(True)
        self.resize(600, 400)

        self.target_dir = target_dir
        self.tree_builder = TreeBuilder()

        # Root node (project name)
        root_item = QStandardItem(os.path.basename(target_dir))
        root_item.setEditable(False)
        root_item.setData(target_dir, Qt.UserRole)  # store real path
        
        self.model = QStandardItemModel()
        self.model.appendRow(root_item)
        self.setModel(self.model)
        
        # Delay tree population to avoid blocking startup
        from PySide6.QtCore import QTimer
        QTimer.singleShot(50, lambda: self.populate_tree(root_item, target_dir, lazy_load=True))

        self.doubleClicked.connect(self.on_double_click)

        # Enable right-click menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)
        
        # Connect expanded/collapsed signals
        self.expanded.connect(self._on_expanded)
        self.collapsed.connect(self._on_collapsed)

    def on_double_click(self, index):
        item = self.model.itemFromIndex(index)
        path = self.get_item_path(item)
        if os.path.isfile(path) and path.endswith(".md"):
            self.file_open_requested.emit(path)

    def open_menu(self, position):
        index = self.indexAt(position)
        if not index.isValid():
            return

        item = self.model.itemFromIndex(index)

        menu = QMenu()
        add_folder_action = menu.addAction("New Folder")
        add_file_action = menu.addAction("New Test Case (.md)")
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        open_dir_action = menu.addAction("Open Directory")  # ✅ new action

        action = menu.exec_(self.viewport().mapToGlobal(position))

        if action == add_folder_action:
            self.add_folder(item)
        elif action == add_file_action:
            self.add_testcase(item)
        elif action == rename_action:
            self.rename_item(item)
        elif action == delete_action:
            self.delete_item(item)
        elif action == open_dir_action:
            self.open_directory(item)  # ✅ call new method

    import subprocess
    import platform

    def open_directory(self, item):
        path = self.get_item_path(item)
        if os.path.isfile(path):
            path = os.path.dirname(path)  # open parent folder if it's a file

        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", path])
            else:  # Linux / Unix
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot open directory: {e}")

    def add_folder(self, parent_item):
        text, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and text:
            new_item = QStandardItem(text)
            new_item.setEditable(False)
            new_item.setIcon(QIcon(resource_path("assets/icons/folder.png")))
            parent_item.appendRow(new_item)

            parent_path = self.get_item_path(parent_item)
            new_path = os.path.join(parent_path, text)
            os.makedirs(new_path, exist_ok=True)
            new_item.setData(new_path, Qt.UserRole)
            self.state_changed.emit()

    def add_testcase(self, parent_item):
        text, ok = QInputDialog.getText(self, "New Test Case", "Enter file name (without extension):")
        if ok and text:
            filename = f"{text}.md"
            new_item = QStandardItem(filename)
            new_item.setEditable(False)
            new_item.setIcon(QIcon(resource_path("assets/icons/testcase_normal.png")))
            parent_item.appendRow(new_item)

            parent_path = self.get_item_path(parent_item)
            new_path = os.path.join(parent_path, filename)
            with open(new_path, "w", encoding="utf-8") as f:
                f.write("# New Test Case\n")
            new_item.setData(new_path, Qt.UserRole)
            self.state_changed.emit()

    def rename_item(self, item):
        text, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=item.text())
        if ok and text:
            old_path = self.get_item_path(item)
            new_path = os.path.join(os.path.dirname(old_path), text)
            try:
                os.rename(old_path, new_path)
                item.setText(text)
                item.setData(new_path, Qt.UserRole)
                self.state_changed.emit()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Rename failed: {e}")

    def delete_item(self, item):
        reply = QMessageBox.question(self, "Delete", f"Delete {item.text()} ?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            path = self.get_item_path(item)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                parent = item.parent() or self.model.invisibleRootItem()
                parent.removeRow(item.row())
                self.state_changed.emit()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Delete failed: {e}")

    def get_item_path(self, item):
        return item.data(Qt.UserRole)
    
    def _on_expanded(self, index):
        """Handle expanded event with lazy loading"""
        item = self.model.itemFromIndex(index)
        if item and item.hasChildren():
            # Check if this is a placeholder (has only one child called "Loading...")
            if item.rowCount() == 1:
                child = item.child(0, 0)
                if child and child.text() == "Loading...":
                    # Remove placeholder
                    item.removeRow(0)
                    # Load actual children with lazy loading for subdirectories
                    path = item.data(Qt.UserRole)
                    self.populate_tree(item, path, lazy_load=True)
        
        self.state_changed.emit()
    
    def _on_collapsed(self, index):
        """Handle collapsed event"""
        self.state_changed.emit()
    
    def get_expanded_state(self) -> list:
        """Get list of expanded folder paths"""
        expanded_paths = []
        self._collect_expanded_paths(self.model.index(0, 0), expanded_paths)
        return expanded_paths
    
    def _collect_expanded_paths(self, index: QModelIndex, expanded_paths: list):
        """Recursively collect expanded folder paths"""
        if not index.isValid():
            return
        
        if self.isExpanded(index):
            item = self.model.itemFromIndex(index)
            path = item.data(Qt.UserRole)
            if path and os.path.isdir(path):
                expanded_paths.append(path)
        
        # Recursively check children
        for row in range(self.model.rowCount(index)):
            child_index = self.model.index(row, 0, index)
            self._collect_expanded_paths(child_index, expanded_paths)
    
    def set_expanded_state(self, expanded_paths: list):
        """Expand folders based on saved paths"""
        if not expanded_paths:
            return
        expanded_set = set(expanded_paths)
        self._restore_expanded_state(self.model.index(0, 0), expanded_set)
        # Trigger state change after restoration to ensure it's saved
        self.state_changed.emit()
    
    def _restore_expanded_state(self, index: QModelIndex, expanded_set: set):
        """Recursively restore expanded state"""
        if not index.isValid():
            return
        
        item = self.model.itemFromIndex(index)
        path = item.data(Qt.UserRole)
        if path and path in expanded_set and os.path.isdir(path):
            # Expand this item
            self.expand(index)
            
            # After expanding, check if we need to load content (lazy loading)
            if item.rowCount() == 1:
                child = item.child(0, 0)
                if child and child.text() == "Loading...":
                    # Remove placeholder and load actual children
                    item.removeRow(0)
                    self.populate_tree(item, path, lazy_load=True)
        
        # Recursively check children (after potential loading)
        for row in range(self.model.rowCount(index)):
            child_index = self.model.index(row, 0, index)
            child_item = self.model.itemFromIndex(child_index)
            child_path = child_item.data(Qt.UserRole)
            
            # If this child should be expanded and has a loading placeholder, load it first
            if child_path and child_path in expanded_set and child_item.rowCount() == 1:
                child = child_item.child(0, 0)
                if child and child.text() == "Loading...":
                    # Remove placeholder and load actual children
                    child_item.removeRow(0)
                    self.populate_tree(child_item, child_path, lazy_load=True)
            
            self._restore_expanded_state(child_index, expanded_set)


    def populate_tree(self, parent_item, path, lazy_load=True):
        """Populate tree with directory contents. If lazy_load=True, only load immediate children."""
        self.tree_builder.populate_tree_from_directory(
            parent_item, 
            path, 
            lazy_load=lazy_load, 
            show_md_files_only=True
        )

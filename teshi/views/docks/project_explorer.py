import sys
import os
import shutil
from PySide6.QtWidgets import (
    QApplication, QTreeView, QMenu, QInputDialog, QMessageBox
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide6.QtCore import Qt
import platform
import subprocess


class ProjectExplorer(QTreeView):
    def __init__(self, target_dir):
        super().__init__()
        self.setWindowTitle("Project Explorer")
        self.setHeaderHidden(True)
        self.resize(600, 400)

        self.target_dir = target_dir

        # Root node (project name)
        root_item = QStandardItem(os.path.basename(target_dir))
        root_item.setEditable(False)
        root_item.setIcon(QIcon("assets/icons/folder.png"))
        root_item.setData(target_dir, Qt.UserRole)  # store real path
        populate_tree(root_item, target_dir)

        self.model = QStandardItemModel()
        self.model.appendRow(root_item)
        self.setModel(self.model)

        # Enable right-click menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)

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
            new_item.setIcon(QIcon("assets/icons/folder.png"))
            parent_item.appendRow(new_item)

            parent_path = self.get_item_path(parent_item)
            new_path = os.path.join(parent_path, text)
            os.makedirs(new_path, exist_ok=True)
            new_item.setData(new_path, Qt.UserRole)

    def add_testcase(self, parent_item):
        text, ok = QInputDialog.getText(self, "New Test Case", "Enter file name (without extension):")
        if ok and text:
            filename = f"{text}.md"
            new_item = QStandardItem(filename)
            new_item.setEditable(False)
            new_item.setIcon(QIcon("assets/icons/testcase_normal.png"))
            parent_item.appendRow(new_item)

            parent_path = self.get_item_path(parent_item)
            new_path = os.path.join(parent_path, filename)
            with open(new_path, "w", encoding="utf-8") as f:
                f.write("# New Test Case\n")
            new_item.setData(new_path, Qt.UserRole)

    def rename_item(self, item):
        text, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=item.text())
        if ok and text:
            old_path = self.get_item_path(item)
            new_path = os.path.join(os.path.dirname(old_path), text)
            try:
                os.rename(old_path, new_path)
                item.setText(text)
                item.setData(new_path, Qt.UserRole)
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
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Delete failed: {e}")

    def get_item_path(self, item):
        return item.data(Qt.UserRole)


def populate_tree(parent_item, path):
    try:
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                item = QStandardItem(entry)
                item.setEditable(False)
                item.setIcon(QIcon("assets/icons/folder.png"))
                item.setData(full_path, Qt.UserRole)
                parent_item.appendRow(item)
                populate_tree(item, full_path)
            else:
                item = QStandardItem(entry)
                item.setEditable(False)
                if full_path.endswith(".md"):
                    item.setIcon(QIcon("assets/icons/testcase_normal.png"))
                else:
                    item.setIcon(QIcon("assets/icons/unknown_file.png"))
                item.setData(full_path, Qt.UserRole)
                parent_item.appendRow(item)
    except PermissionError:
        pass

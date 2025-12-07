import os
from PySide6.QtWidgets import QApplication, QTreeView
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon


class ProjectExplorer(QTreeView):
    def __init__(self, target_dir):
        super().__init__()
        self.setWindowTitle("Project structure tree")
        self.setHeaderHidden(True)
        self.resize(600, 400)

        root_item = QStandardItem(os.path.basename(target_dir))
        root_item.setEditable(False)
        root_item.setIcon(QIcon("assets/icons/folder.png"))
        populate_tree(root_item, target_dir)

        model = QStandardItemModel()
        model.appendRow(root_item)
        self.setModel(model)

def populate_tree(parent_item, path):
    try:
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                item = QStandardItem(entry)
                item.setEditable(False)
                item.setIcon(QIcon("assets/icons/folder.png"))
                parent_item.appendRow(item)
                populate_tree(item, full_path)
            else:
                item = QStandardItem(entry)
                item.setEditable(False)
                # if file name ends with .md, use testcase_normal icon
                if full_path.endswith(".md"):
                    item.setIcon(QIcon("assets/icons/testcase_normal.png"))
                else:
                    item.setIcon(QIcon("assets/icons/unknown_file.png"))
                parent_item.appendRow(item)

    except PermissionError:
        pass



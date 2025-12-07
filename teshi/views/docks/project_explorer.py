import os
from PySide6.QtWidgets import QApplication, QTreeView
from PySide6.QtGui import QStandardItemModel, QStandardItem


class ProjectExplorer(QTreeView):
    def __init__(self, target_dir):
        super().__init__()
        self.setWindowTitle("Project structure tree")
        self.setHeaderHidden(True)
        self.resize(600, 400)

        root_item = QStandardItem(os.path.basename(target_dir))
        root_item.setEditable(False)
        populate_tree(root_item, target_dir)

        model = QStandardItemModel()
        model.appendRow(root_item)
        self.setModel(model)



def populate_tree(parent_item, path):
    try:
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            item = QStandardItem(entry)
            item.setEditable(False)
            parent_item.appendRow(item)

            if os.path.isdir(full_path):
                populate_tree(item, full_path)
    except PermissionError:
        pass



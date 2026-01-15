from PySide6.QtWidgets import QWidget

class YamlTab(QWidget):
    def __init__(self, title, tab_id, notebook_dir, file_path, graph_data, scene, view):
        super().__init__()
        self.title = title
        self.tab_id = tab_id
        self.notebook_dir = notebook_dir
        self.file_path = file_path
        self.graph_data = graph_data
        self.scene = scene
        self.view = view

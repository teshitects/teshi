import sys
import uuid
import datetime
from pathlib import Path

from PySide6 import QtGui, QtWidgets, QtCore
from PySide6.QtCore import QSettings, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QListWidget, QTextEdit, QPushButton, QFrame, QMessageBox, QApplication
)
from PySide6.QtGui import QColor, QAction

from teshi.utils.graph_execute_controller import GraphExecuteController
from teshi.models.jupyter_node_model import JupyterNodeModel
from teshi.utils.ipynb_file_util import load_notebook, save_notebook, add_cell, remove_cell
from teshi.views.widgets.automate_widget import NodeSketchpadView, NodeSketchpadScene, JupyterGraphNode
from teshi.views.widgets.component.automate_connection_item import ConnectionItem
from teshi.views.widgets.component.automate_connection_item import ConnectionItem
from teshi.config.automate_editor_config import AutomateEditorConfig
from teshi.views.widgets.automate_browser_widget import AutomateBrowserWidget
from teshi.utils import graph_util

class AutomateModeWidget(QWidget):
    """
    Widget for Automate mode (IPyKernel Script Runner).
    Embedded inside EditorWidget.
    """
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        # .ipynb path is same as source file but with .ipynb extension
        self.notebook_path = str(Path(file_path).with_suffix('.ipynb'))
        self.notebook_dir = str(Path(file_path).parent.resolve())
        
        # Unique tab ID for this session (used for binding messages)
        self.tab_id = str(uuid.uuid1())
        
        self.notebook = None
        self.scene = None
        self.view = None
        
        self.thread1 = None
        
        self.setup_ui()
        self.load_notebook_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main Splitter: Canvas (Left/Center) vs Docks (Right/Bottom)
        # To mimic the Dock layout in QMainWindow, we use QSplitters.
        # Layout:
        # ------------------------------
        # |        |       Raw         |
        # | Canvas |-------------------|
        # |        |      Result       |
        # ------------------------------
        # |          Logger            |
        # ------------------------------
        # |         Buttons            |
        # ------------------------------
        
        # Splitter 0: Browser (Left) vs Main (Center+Right)
        self.root_splitter = QSplitter(Qt.Horizontal)

        # Browser Widget (Left)
        # Assuming we can get project dir from notebook path or passed in. 
        # Using notebook_dir as project root for now, or we might need a better way to find root.
        # But 'notebook_dir' is usually just the folder of the current file.
        # Ideally we should use the parent project root if possible.
        # For now, let's use self.notebook_dir as a starting point.
        self.browser_widget = AutomateBrowserWidget(self.notebook_dir)
        self.root_splitter.addWidget(self.browser_widget)

        # Splitter 1: Top (Canvas+Side) vs Bottom (Logger)
        self.main_splitter = QSplitter(Qt.Vertical)

        
        # Splitter 2: Canvas vs Right Side (Raw/Result)
        self.center_splitter = QSplitter(Qt.Horizontal)
        
        # Canvas Container
        self.canvas_container = QWidget()
        self.canvas_layout = QVBoxLayout(self.canvas_container)
        self.canvas_layout.setContentsMargins(0, 0, 0, 0)
        
        # Right Side Container
        self.right_container = QWidget()
        self.right_layout = QVBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Raw Code Area
        self.right_layout.addWidget(QtWidgets.QLabel("Raw Code"))
        self.raw_code_widget = QTextEdit()
        self.raw_code_widget.setLineWrapMode(QTextEdit.NoWrap)
        self.raw_code_widget.setFont(AutomateEditorConfig.node_title_font)
        self.right_layout.addWidget(self.raw_code_widget)
        
        # Result Area
        self.right_layout.addWidget(QtWidgets.QLabel("Result"))
        self.result_widget = QTextEdit()
        self.result_widget.setReadOnly(True)
        self.result_widget.setFont(AutomateEditorConfig.node_title_font)
        self.result_widget.setLineWrapMode(QTextEdit.NoWrap)
        self.right_layout.addWidget(self.result_widget)
        
        # Add to Center Splitter
        self.center_splitter.addWidget(self.canvas_container)
        self.center_splitter.addWidget(self.right_container)
        self.center_splitter.setStretchFactor(0, 3) # Canvas takes 3 parts
        self.center_splitter.setStretchFactor(1, 1) # Right side takes 1 part
        
        # Logger Area
        self.logger_container = QWidget()
        self.logger_layout = QVBoxLayout(self.logger_container)
        self.logger_layout.setContentsMargins(0, 0, 0, 0)
        self.logger_layout.addWidget(QtWidgets.QLabel("Logger"))
        self.logger_widget = QTextEdit()
        self.logger_widget.setReadOnly(True)
        self.logger_widget.setLineWrapMode(QTextEdit.NoWrap)
        self.logger_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.logger_widget.setFrameStyle(QFrame.NoFrame)
        self.logger_layout.addWidget(self.logger_widget)
        
        # Add to Main Splitter
        self.main_splitter.addWidget(self.center_splitter)
        self.main_splitter.addWidget(self.logger_container)
        self.main_splitter.setStretchFactor(0, 4)
        self.main_splitter.setStretchFactor(1, 1)
        
        self.main_splitter.addWidget(self.center_splitter)
        self.main_splitter.addWidget(self.logger_container)
        self.main_splitter.setStretchFactor(0, 4)
        self.main_splitter.setStretchFactor(1, 1)

        self.root_splitter.addWidget(self.main_splitter)
        self.root_splitter.setStretchFactor(0, 1) # Browser
        self.root_splitter.setStretchFactor(1, 4) # Main Content
        
        layout.addWidget(self.root_splitter)
        
        # Button Group (Bottom)
        self.button_group = QWidget()
        self.button_layout = QHBoxLayout(self.button_group)
        self.button_layout.setContentsMargins(5, 5, 5, 5)
        
        save_code_button = QPushButton("Save Code")
        save_code_button.clicked.connect(self.update_graph_node_code)
        
        run_single_node_button = QPushButton("Run Single")
        run_single_node_button.clicked.connect(self.run_single_node_and_parent)
        
        run_button = QPushButton("Run ALL")
        run_button.clicked.connect(self.run_all)
        
        restore_button = QPushButton("Restore Status")
        restore_button.clicked.connect(self.restore)
        
        self.button_layout.addWidget(save_code_button)
        self.button_layout.addWidget(run_single_node_button)
        self.button_layout.addWidget(run_button)
        self.button_layout.addWidget(restore_button)
        self.button_layout.addStretch()
        
        layout.addWidget(self.button_group)


    def load_notebook_data(self):
        # Update Browser widget
        self.browser_widget.refresh_project_nodes()

        # Ensure file exists, create empty if not
        if not Path(self.notebook_path).exists():
             self.create_empty_notebook()
             
        self.notebook = load_notebook(self.notebook_path)
        
        if self.notebook.metadata.get("scene_data"):
            items_data = self.notebook.metadata.get("scene_data")
        else:
            items_data = {}

        # Init Scene and View
        self.scene = NodeSketchpadScene(self)
        self.view = NodeSketchpadView(self.scene, self)
        self.view.setAlignment(Qt.AlignCenter)
        
        # Add view to layout
        # Clear previous if any
        if self.canvas_layout.count() > 0:
             self.canvas_layout.itemAt(0).widget().deleteLater()
        self.canvas_layout.addWidget(self.view)
        
        # Load Nodes from Notebook Cells
        nodes = []
        for cell in self.notebook.cells:
            if cell.cell_type == 'code':
                # First line as title
                title = cell.source.split('\n')[0]
                node_model = JupyterNodeModel(title, cell.source)
                node_model.tab_id = self.tab_id
                nodes.append(node_model)
        
        graph_nodes = {}
        # Draw Nodes
        # Basic layout strategy: Horizontal line if no position data
        for index, node in enumerate(nodes):
            if node.title in graph_nodes:
                continue
                
            rect = JupyterGraphNode(node.title, node.code)
            graph_nodes[node.title] = rect
            
            # Position
            if node.title in items_data:
                 rect.setPos(items_data[node.title]['x'], items_data[node.title]['y'])
            else:
                 rect.setPos(index * 300, 0)
            
            rect.signals.nodeClicked.connect(self.update_widget)
            self.scene.addItem(rect)
            
        # Draw Connections
        # "children" in scene_data are connections
        for node_title, rect in graph_nodes.items():
            if node_title in items_data:
                data = items_data[node_title]
                if 'children' in data:
                    for child_title in data['children']:
                        if child_title in graph_nodes:
                            target_rect = graph_nodes[child_title]
                            # Check if connection already exists to avoid dupes if data is messy
                            existing = False
                            for conn in rect.connections:
                                if conn.destination == target_rect:
                                    existing = True
                                    break
                            if not existing:
                                connection = ConnectionItem(rect, target_rect)
                                self.scene.addItem(connection)
                                rect.add_connection(connection)
                                target_rect.add_connection(connection)

        self.update_browser_canvas_nodes()

    def update_browser_canvas_nodes(self):
        """Update the execution order list in the browser widget"""
        try:
             # Build graph for topo sort
             graph = {item.data_model.title: item.data_model.children for item in self.scene.items() if isinstance(item, JupyterGraphNode)}
             
             # Calculate topological order
             topo_order = graph_util.topological_sort(graph)
             
             self.browser_widget.update_canvas_nodes(topo_order)
        except Exception as e:
             print(f"Error updating canvas nodes list: {e}")


    def create_empty_notebook(self):
        import nbformat
        nb = nbformat.v4.new_notebook()
        with open(self.notebook_path, 'w', encoding='utf-8') as f:
            nbformat.write(nb, f)

    def update_widget(self, data_model_dict):
        """Update side panel when a node is clicked"""
        self.raw_code_widget.setText(data_model_dict["code"])
        self.result_widget.setText(data_model_dict.get("result", ""))
        # set uuid in tooltip to identify which node is selected
        self.result_widget.setToolTip(data_model_dict['uuid'])

    def update_graph_node_code(self):
        """Save code from Raw Code widget to the selected node"""
        uuid = self.result_widget.toolTip()
        if not uuid:
            return
            
        for item in self.scene.items():
            if isinstance(item, JupyterGraphNode):
                if item.data_model.uuid == uuid:
                    item.data_model.code = self.raw_code_widget.toPlainText()
                    item.data_model.code_changed = True
                    # Check if title changed (first line)
                    new_title = item.data_model.code.split('\n')[0]
                    if new_title != item.data_model.title:
                        self.item_title_changed(item, new_title)
                    self.save_notebook_file() # Auto save to file
                    break

    def item_title_changed(self, item, new_title):
        old_title = item.data_model.title
        
        # Update notebook cells
        notebook_item_titles = [cell.source.split('\n')[0] for cell in self.notebook.cells if cell.cell_type == 'code']
        if old_title in notebook_item_titles:
             idx = notebook_item_titles.index(old_title)
             self.notebook.cells[idx].source = item.data_model.code
             
        # Update connections references (children list in other nodes)
        for scene_item in self.scene.items():
            if isinstance(scene_item, JupyterGraphNode):
                if old_title in scene_item.data_model.children:
                    scene_item.data_model.children.remove(old_title)
                    scene_item.data_model.children.append(new_title)
        
        item.data_model.title = new_title
        item._title = new_title
        item.set_title_text(new_title)

    def save_notebook_file(self):
        """Sync scene to notebook and save file"""
        # 1. Sync Logic (Add new nodes, remove deleted nodes, update code)
        # Identify current nodes in scene
        scene_nodes = {item.data_model.title: item for item in self.scene.items() if isinstance(item, JupyterGraphNode)}
        
        # Identify current cells in notebook
        notebook_cells = {cell.source.split('\n')[0]: cell for cell in self.notebook.cells if cell.cell_type == 'code'}
        
        # A. Add new nodes to notebook
        for title, item in scene_nodes.items():
            if title not in notebook_cells:
                add_cell(self.notebook, item.data_model.code)
                
        # B. Remove deleted nodes from notebook
        # Note: Removing while iterating needs care, better to rebuild list or use index
        # Re-eval notebook cells list
        current_titles = [cell.source.split('\n')[0] for cell in self.notebook.cells if cell.cell_type == 'code']
        for title in current_titles:
            if title not in scene_nodes:
                # Find index
                for i, cell in enumerate(self.notebook.cells):
                    if cell.cell_type == 'code' and cell.source.split('\n')[0] == title:
                        remove_cell(self.notebook, i)
                        break
                        
        # C. Update code content
        for i, cell in enumerate(self.notebook.cells):
            if cell.cell_type == 'code':
                title = cell.source.split('\n')[0]
                if title in scene_nodes:
                     item = scene_nodes[title]
                     # If code changed in item but not saved to cell yet
                     if item.data_model.code != cell.source:
                         cell.source = item.data_model.code

        self.update_browser_canvas_nodes()
                         
        # D. Update Scene Data (Metadata)
        items_data = {item.data_model.title: item.to_dict() for item in self.scene.items() if isinstance(item, JupyterGraphNode)}
        self.notebook.metadata["scene_data"] = items_data
        self.notebook.metadata["last_modified"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.notebook.metadata["last_modified_by"] = "Teshi Automate"
        
        save_notebook(self.notebook, self.notebook_path)

    def restore(self):
        for item in self.scene.items():
            if isinstance(item, JupyterGraphNode):
                item.set_default_color()
                item.set_default_text()
                item.data_model.last_status = ""
                
    def run_all(self):
        self.save_notebook_file() # Save before run
        self.restore()
        
        graph = {item.data_model.title: item.data_model.children for item in self.scene.items() if isinstance(item, JupyterGraphNode)}
        nodes_data = {item.data_model.title:[item.data_model.code, item.data_model.uuid] for item in self.scene.items() if isinstance(item, JupyterGraphNode)}
        
        if self.thread1 is not None:
             self.thread1.quit()
             self.thread1.wait()
             
        self.thread1 = QtCore.QThread()
        self.worker = GraphExecuteController(graph, nodes_data, self.notebook_dir, self.tab_id)
        self.worker.moveToThread(self.thread1)
        self.worker.executor_process.connect(self.update_process)
        self.worker.executor_binding.connect(self.bind_item_msg_id)
        self.thread1.started.connect(self.worker.execute_all)
        self.thread1.start()

    def run_single_node_and_parent(self):
        selected_items = self.scene.selectedItems()
        if not selected_items or not isinstance(selected_items[0], JupyterGraphNode):
            QMessageBox.information(self, "Info", "Please select a node first.")
            return

        self.save_notebook_file()
        self.restore()
        
        target_node = selected_items[0]
        graph = {item.data_model.title: item.data_model.children for item in self.scene.items() if isinstance(item, JupyterGraphNode)}
        nodes_data = {item.data_model.title:[item.data_model.code, item.data_model.uuid] for item in self.scene.items() if isinstance(item, JupyterGraphNode)}
        
        if self.thread1 is not None:
             self.thread1.quit()
             self.thread1.wait()
             
        self.thread1 = QtCore.QThread()
        self.worker = GraphExecuteController(graph, nodes_data, self.notebook_dir, self.tab_id, target_node.data_model.title)
        self.worker.moveToThread(self.thread1)
        self.worker.executor_process.connect(self.update_process)
        self.worker.executor_binding.connect(self.bind_item_msg_id)
        self.thread1.started.connect(self.worker.execute_single_node_and_its_parents)
        self.thread1.start()

    def bind_item_msg_id(self, binding):
        """Bind execution message ID to node UUID"""
        # format: msg_id:tab_id#item_uuid
        parts = binding.split(":")
        if len(parts) < 2: return
        msg_id = parts[0]
        
        rest = parts[1]
        if "#" not in rest: return
        t_id, item_id = rest.split("#")
        
        if t_id != self.tab_id: return
        
        self.logger_widget.append(f"Binding: {binding}")
        
        for item in self.scene.items():
            if isinstance(item, JupyterGraphNode):
                if item.data_model.uuid == item_id:
                    item.data_model.msg_id = msg_id

    def update_process(self, process):
        # format: msg_id:tab_id:status_info
        # Actually logic in automate_engine.py is:
        # parent_msg_id#tab_id:status:idle
        
        if "#" not in process: 
             self.logger_widget.append(process)
             return
             
        first_part = process.split(":")[0]
        if "#" not in first_part: return
        
        msg_id, t_id = first_part.split("#")
        
        if t_id != self.tab_id: return
        
        # Remove prefix to get content
        status_str = process[len(first_part)+1:]
        
        for item in self.scene.items():
            if isinstance(item, JupyterGraphNode):
                if getattr(item.data_model, 'msg_id', None) == msg_id:
                     self._update_node_status(item, status_str)
        
        self.logger_widget.append(process)

    def _update_node_status(self, item, status_str):
        if status_str == "status:busy":
            item.set_color(QColor('yellow'))
            item.data_model.last_status = "status:busy"
        elif status_str.startswith("execute_input"):
            item.set_color(QColor('yellow'))
            item.data_model.last_status = "execute_input"
        elif status_str == "status:idle":
            if item.data_model.last_status != "error":
                item.set_color(QColor('green'))
                item.data_model.last_status = "idle"
        elif status_str.startswith("error"):
            item.set_color(QColor('red'))
            item.data_model.last_status = "error"
            error_msg = status_str.replace("error_:", "")
            item.set_result_text(error_msg.split("\n")[0])
            item.data_model.result = error_msg
            # Update result widget if this node is selected
            if self.result_widget.toolTip() == item.data_model.uuid:
                 self.result_widget.setText(error_msg)
        elif status_str.startswith("stream"):
            item.data_model.last_status = "stream"
            stream_msg = status_str.replace("stream:", "")
            item.set_result_text(stream_msg.split("\n")[0])
            item.data_model.result = stream_msg
            if self.result_widget.toolTip() == item.data_model.uuid:
                 self.result_widget.setText(stream_msg)

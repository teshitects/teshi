import os
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
from teshi.services.node_registry_service import NodeRegistryService
from teshi.utils import graph_util
from teshi.utils.yaml_graph_util import save_graph_to_yaml
from teshi.views.widgets.component.python_highlighter import PythonHighlighter

class RawCodeEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_text = ""
        self.save_btn_ref = None

    def set_text_with_original(self, text):
        self.setPlainText(text)
        self.original_text = text

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        # Check if content changed
        if self.toPlainText() != self.original_text:
            # Defer check to allow focus to settle (e.g. if moving to Save button)
            QtCore.QTimer.singleShot(50, self.check_abandon)

    def check_abandon(self):
        # If focus moved to the save button, don't show dialog
        if self.save_btn_ref and QApplication.focusWidget() == self.save_btn_ref:
            return

        # If we are not visible (e.g. tab switch hidden us), maybe skip?
        # But requirement says "lose focus".

        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Save modifications?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Save the changes
            self.save_btn_ref.click()
        else:
            # Revert to original text
            self.setPlainText(self.original_text)


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
        self.parent_widget = parent

        # Initialize Node Registry Service
        # Try to find project root by looking for .teshi
        project_root = self.notebook_dir
        while project_root and project_root != str(Path(project_root).parent):
            if  os.path.exists(os.path.join(project_root, '.teshi')):
                break
            project_root = str(Path(project_root).parent)
        
        self.node_registry = NodeRegistryService(project_root)

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
        self.root_splitter.splitterMoved.connect(self._on_splitter_moved)

        # Browser Widget (Left)
        # Assuming we can get project dir from notebook path or passed in.
        # Using notebook_dir as project root for now, or we might need a better way to find root.
        # But 'notebook_dir' is usually just the folder of the current file.
        # Ideally we should use the parent project root if possible.
        # For now, let's use self.notebook_dir as a starting point.
        self.browser_widget = AutomateBrowserWidget(self.notebook_dir, self.node_registry, self)
        self.root_splitter.addWidget(self.browser_widget)


        # Splitter 1: Top (Canvas+Side) vs Bottom (Logger)
        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.splitterMoved.connect(self._on_splitter_moved)


        # Splitter 2: Canvas vs Right Side (Raw/Result)
        self.center_splitter = QSplitter(Qt.Horizontal)
        self.center_splitter.splitterMoved.connect(self._on_splitter_moved)

        
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
        
        # Container for Raw Code + Save Button (Overlay or Layout)
        # Using a layout approach: Editor takes expanding space, Button at bottom right
        self.raw_code_container = QWidget()
        self.raw_code_container_layout = QVBoxLayout(self.raw_code_container)
        self.raw_code_container_layout.setContentsMargins(0, 0, 0, 0)
        self.raw_code_container_layout.setSpacing(2)
        
        self.raw_code_widget = RawCodeEditor()
        self.raw_code_widget.setLineWrapMode(QTextEdit.NoWrap)
        self.raw_code_widget.setFont(AutomateEditorConfig.node_title_font)
        # Dark styling for code editor
        self.raw_code_widget.setStyleSheet(f"background-color: {AutomateEditorConfig.scene_background_color}; color: white;")
        
        # Attach Syntax Highlighter
        self.highlighter = PythonHighlighter(self.raw_code_widget.document())
        
        self.raw_code_widget.textChanged.connect(self._trigger_workspace_save)
        
        self.raw_code_container_layout.addWidget(self.raw_code_widget)
        
        # Save Button Layout (Right Aligned)
        self.save_code_layout = QHBoxLayout()
        self.save_code_layout.addStretch()
        
        self.save_code_button = QPushButton("Save Code")
        self.save_code_button.setCursor(Qt.PointingHandCursor)
        # Make save button more prominent
        self.save_code_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        # Connect later or here? Connected in separate block before, do it here to ensure ref availability
        self.save_code_button.clicked.connect(self.update_graph_node_code)
        
        self.save_code_layout.addWidget(self.save_code_button)
        self.raw_code_container_layout.addLayout(self.save_code_layout)
        
        # Link button ref to editor for focus check
        self.raw_code_widget.save_btn_ref = self.save_code_button
        
        self.right_layout.addWidget(self.raw_code_container)

        
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
        
        # Add everything to root
        self.root_splitter.addWidget(self.main_splitter)
        
        # Set default absolute sizes (pixel widths)
        # root_splitter: Browser (Left) vs Main (Right)
        self.root_splitter.setSizes([200, 1000])
        
        # main_splitter: Center Splitter (Top) vs Logger (Bottom)
        self.main_splitter.setSizes([800, 200])
        
        # center_splitter: Canvas (Left) vs Right Side (Raw/Result)
        self.center_splitter.setSizes([850, 350])
        
        layout.addWidget(self.root_splitter)
        
        # Button Group (Bottom)
        self.button_group = QWidget()
        self.button_layout = QHBoxLayout(self.button_group)
        self.button_layout.setContentsMargins(5, 5, 5, 5)
        
        
        run_single_node_button = QPushButton("Run Single")
        run_single_node_button.clicked.connect(self.run_single_node_and_parent)
        
        run_button = QPushButton("Run ALL")
        run_button.clicked.connect(self.run_all)
        
        restore_button = QPushButton("Restore Status")
        restore_button.clicked.connect(self.restore)
        
        # self.button_layout.addWidget(save_code_button) # Removed, moved to Raw Code area
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
        
        # Load items_data from ipynb metadata (legacy/fallback)
        ipynb_items_data = self.notebook.metadata.get("scene_data", {})
        
        # Problem 3: Also try to load from YAML file (primary source for params)
        yaml_path = str(Path(self.file_path).with_suffix('.yaml'))
        yaml_graph_data = {}
        if os.path.exists(yaml_path):
            from teshi.utils.yaml_graph_util import load_graph_from_yaml
            yaml_graph_data = load_graph_from_yaml(yaml_path)
        
        # Build items_data from YAML (keyed by title for compatibility)
        yaml_items_data = {}
        for node_info in yaml_graph_data.get('nodes', []):
            title = node_info.get('title', '')
            if title:
                yaml_items_data[title] = {
                    'x': node_info.get('pos', [0, 0])[0],
                    'y': node_info.get('pos', [0, 0])[1],
                    'params': node_info.get('params', {}),
                    'node_type': node_info.get('node_type', ''),
                    'uuid': node_info.get('id', '')
                }
        
        # Merge: YAML takes priority for params/pos, ipynb for children/connections
        items_data = {}
        all_titles = set(ipynb_items_data.keys()) | set(yaml_items_data.keys())
        for title in all_titles:
            ipynb_item = ipynb_items_data.get(title, {})
            yaml_item = yaml_items_data.get(title, {})
            items_data[title] = {
                'x': yaml_item.get('x', ipynb_item.get('x', 0)),
                'y': yaml_item.get('y', ipynb_item.get('y', 0)),
                'params': yaml_item.get('params', ipynb_item.get('params', {})),
                'node_type': yaml_item.get('node_type', ipynb_item.get('node_type', '')),
                'uuid': yaml_item.get('uuid', ipynb_item.get('uuid', '')),
                'children': ipynb_item.get('children', []),  # Connections from ipynb
            }

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
                 if 'params' in items_data[node.title]:
                     rect.data_model.params = items_data[node.title]['params']
                 
                 # Problem 3: If YAML has node_type, try to load code from registry
                 node_type = items_data[node.title].get('node_type')
                 if node_type:
                     rect.data_model.node_type = node_type
                     registry_data = self.node_registry.get_node_data(node_type)
                     if registry_data:
                         rect.data_model.code = registry_data['code']
                         # Important: If it's the first time, we might need to update title too
                         # but title is already set from notebook cells loop above
                 
                 rect.update_input_widgets()
            else:
                 rect.setPos(index * 300, 0)
            
            # Register code if not already in registry
            if rect.data_model.code:
                node_type = self.node_registry.register_node(rect.data_model.title, rect.data_model.code)
                rect.data_model.node_type = node_type

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
        self.raw_code_widget.set_text_with_original(data_model_dict["code"])
        self.result_widget.setText(data_model_dict.get("result", ""))
        # set uuid in tooltip to identify which node is selected
        self.result_widget.setToolTip(data_model_dict['uuid'])
        # Trigger workspace save when node selection changes
        self._trigger_workspace_save()


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
                    
                    # Register updated code
                    node_type = self.node_registry.register_node(item.data_model.title, item.data_model.code)
                    item.data_model.node_type = node_type
                    
                    self.save_notebook_file() # Auto save to file
                    
                    # Update original text to match saved version (prevent unsaved prompt)
                    self.raw_code_widget.original_text = self.raw_code_widget.toPlainText()
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

        # E. Always sync to YAML file (same name as source but with .yaml extension)
        # This stores node references and params separately from code
        self.sync_to_yaml()

    def sync_to_yaml(self):
        """Sync current graph structure and params to YAML file (always alongside the test case)"""
        # Generate yaml path from file_path (replace extension with .yaml)
        yaml_path = str(Path(self.file_path).with_suffix('.yaml'))
        
        nodes_data = []
        connections_data = []

        # Nodes
        for item in self.scene.items():
            if isinstance(item, JupyterGraphNode):
                 node_data = {
                        "id": item.data_model.uuid,
                        "title": item.data_model.title,
                        "node_type": item.data_model.node_type, # Added for Problem 3
                        "pos": [item.pos().x(), item.pos().y()],
                        "params": item.data_model.params
                    }
                 nodes_data.append(node_data)

                 # Ensure it is registered
                 if item.data_model.code:
                     self.node_registry.register_node(item.data_model.title, item.data_model.code)

        # Connections
        visited_conns = set()
        for item in self.scene.items():
             if isinstance(item, ConnectionItem):
                  if item in visited_conns:
                       continue
                  visited_conns.add(item)
                  
                  conn_data = {
                        "from": item.source.data_model.title,
                        "to": item.destination.data_model.title
                  }
                  connections_data.append(conn_data)
                  
        graph_data = {
            "nodes": nodes_data,
            "connections": connections_data
        }
        
        try:
             save_graph_to_yaml(graph_data, yaml_path)
        except Exception as e:
             print(f"Failed to sync to YAML: {e}")

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
        nodes_data = {item.data_model.title:[item.data_model.code, item.data_model.uuid, item.data_model.params] for item in self.scene.items() if isinstance(item, JupyterGraphNode)}
        
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
        nodes_data = {item.data_model.title:[item.data_model.code, item.data_model.uuid, item.data_model.params] for item in self.scene.items() if isinstance(item, JupyterGraphNode)}
        
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
                 # Trigger workspace save when error is updated
                 self._trigger_workspace_save()
        elif status_str.startswith("stream"):

            item.data_model.last_status = "stream"
            stream_msg = status_str.replace("stream:", "")
            item.set_result_text(stream_msg.split("\n")[0])
            item.data_model.result = stream_msg
            if self.result_widget.toolTip() == item.data_model.uuid:
                 self.result_widget.setText(stream_msg)
                 # Trigger workspace save when result is updated
                 self._trigger_workspace_save()

    def get_automate_state(self):

        """Get current Automate interface state for workspace saving"""
        state = {
            'project_nodes': [],
            'execution_order': [],
            'raw_code': '',
            'result': '',
            'selected_node_uuid': self.result_widget.toolTip(),
            'browser_search_text': self.browser_widget.search_bar.text(),
            'splitter_sizes': {
                'root_splitter': self.root_splitter.sizes(),
                'main_splitter': self.main_splitter.sizes(),
                'center_splitter': self.center_splitter.sizes(),
                'browser_splitter': self.browser_widget.splitter.sizes()
            }
        }

        # Save project nodes (from browser widget)
        for i in range(self.browser_widget.project_list.count()):
            item = self.browser_widget.project_list.item(i)
            if item and not item.isHidden():
                state['project_nodes'].append({
                    'title': item.text(),
                    'code': item.data(Qt.UserRole) if item.data(Qt.UserRole) else ''
                })

        # Save execution order (canvas nodes)
        for i in range(self.browser_widget.canvas_list.count()):
            item = self.browser_widget.canvas_list.item(i)
            if item:
                state['execution_order'].append(item.text())

        # Save raw code and result if a node is selected
        if state['selected_node_uuid']:
            state['raw_code'] = self.raw_code_widget.toPlainText()
            state['result'] = self.result_widget.toPlainText()

        return state

    def restore_automate_state(self, state):
        """Restore Automate interface state from workspace"""
        try:
            # Check for global layout state from main window first
            if self.parent_widget:
                main_window = self.parent_widget
                while main_window and not hasattr(main_window, 'workspace_manager'):
                    main_window = main_window.parent()

                if main_window and hasattr(main_window, '_global_automate_layout'):
                    # Apply global layout first (workspace-level settings)
                    self.apply_global_layout_state(main_window._global_automate_layout)

            # Restore browser search text
            if 'browser_search_text' in state:
                self.browser_widget.search_bar.setText(state['browser_search_text'])

            # Restore raw code and result for selected node
            if state.get('selected_node_uuid'):
                self.result_widget.setToolTip(state['selected_node_uuid'])
                if 'raw_code' in state:
                    self.raw_code_widget.setText(state['raw_code'])
                if 'result' in state:
                    self.result_widget.setText(state['result'])

            # Restore splitter sizes with delay to ensure UI is fully loaded
            if 'splitter_sizes' in state:
                from PySide6.QtCore import QTimer
                splitter_sizes = state['splitter_sizes']

                def restore_splitter_sizes():
                    """Restore all splitter sizes"""
                    try:
                        # Restore root splitter (Browser vs Main)
                        if 'root_splitter' in splitter_sizes and len(splitter_sizes['root_splitter']) == 2:
                            sizes = splitter_sizes['root_splitter']
                            if sizes[0] > 0 and sizes[1] > 0:
                                self.root_splitter.setSizes(sizes)

                        # Restore main splitter (Canvas vs Logger)
                        if 'main_splitter' in splitter_sizes and len(splitter_sizes['main_splitter']) == 2:
                            sizes = splitter_sizes['main_splitter']
                            if sizes[0] > 0 and sizes[1] > 0:
                                self.main_splitter.setSizes(sizes)

                        # Restore center splitter (Canvas vs Right side)
                        if 'center_splitter' in splitter_sizes and len(splitter_sizes['center_splitter']) == 2:
                            sizes = splitter_sizes['center_splitter']
                            if sizes[0] > 0 and sizes[1] > 0:
                                self.center_splitter.setSizes(sizes)

                        # Restore browser splitter (Project nodes vs Execution order)
                        if 'browser_splitter' in splitter_sizes and len(splitter_sizes['browser_splitter']) == 2:
                            sizes = splitter_sizes['browser_splitter']
                            if sizes[0] > 0 and sizes[1] > 0:
                                self.browser_widget.splitter.setSizes(sizes)
                    except Exception as e:
                        print(f"Error restoring splitter sizes: {e}")

                # Use QTimer to delay restoration until UI is fully loaded
                QTimer.singleShot(100, restore_splitter_sizes)

        # Note: Project nodes and execution order are dynamically managed
        # and don't need explicit restoration as they are loaded from the notebook

        except Exception as e:
            print(f"Error restoring Automate state: {e}")


    def _trigger_workspace_save(self):
        """Trigger workspace save through parent widget"""
        if self.parent_widget:
            # Find main window to trigger workspace save
            main_window = self.parent_widget
            while main_window and not hasattr(main_window, 'workspace_manager'):
                main_window = main_window.parent()

            if main_window and hasattr(main_window, 'workspace_manager'):
                main_window.workspace_manager.trigger_save()

    def get_global_layout_state(self):
        """Get global layout state that should be shared across all automate tabs"""
        return {
            'browser_width': self.root_splitter.sizes()[0] if len(self.root_splitter.sizes()) > 0 else None,
            'result_width': self.center_splitter.sizes()[1] if len(self.center_splitter.sizes()) > 1 else None,
            'logger_height': self.main_splitter.sizes()[1] if len(self.main_splitter.sizes()) > 1 else None
        }

    def apply_global_layout_state(self, state, broadcast=False):
        """Apply global layout state from workspace

        Args:
            state: The layout state to apply
            broadcast: Whether to broadcast the change to other tabs
        """
        if not state:
            return

        # Apply browser width
        if state.get('browser_width') is not None:
            current_sizes = self.root_splitter.sizes()
            if len(current_sizes) == 2:
                total_width = sum(current_sizes)
                new_sizes = [state['browser_width'], total_width - state['browser_width']]
                self.root_splitter.setSizes(new_sizes)

        # Apply result width
        if state.get('result_width') is not None:
            current_sizes = self.center_splitter.sizes()
            if len(current_sizes) == 2:
                total_width = sum(current_sizes)
                new_sizes = [total_width - state['result_width'], state['result_width']]
                self.center_splitter.setSizes(new_sizes)

        # Apply logger height
        if state.get('logger_height') is not None:
            current_sizes = self.main_splitter.sizes()
            if len(current_sizes) == 2:
                total_height = sum(current_sizes)
                new_sizes = [total_height - state['logger_height'], state['logger_height']]
                self.main_splitter.setSizes(new_sizes)

        # Broadcast layout change to all tabs if requested
        if broadcast and self.parent_widget:
            main_window = self.parent_widget
            while main_window and not hasattr(main_window, 'workspace_manager'):
                main_window = main_window.parent()

            if main_window and hasattr(main_window, 'workspace_manager'):
                # Update the global layout in main window
                main_window._global_automate_layout = self.get_global_layout_state()
                # Notify other tabs through workspace manager
                main_window.workspace_manager.trigger_save()

    def _on_splitter_moved(self, pos, index):
        """Handle splitter move events for global layout updates"""
        # First, trigger regular workspace save
        self._trigger_workspace_save()

        # Then, if this is the active tab, update global layout and broadcast to other tabs
        if self.parent_widget:
            main_window = self.parent_widget
            while main_window and not hasattr(main_window, 'tabs'):
                main_window = main_window.parent()

            if main_window and hasattr(main_window, 'tabs'):
                # Check if this widget is the current active tab
                if main_window.tabs.currentWidget() == self:
                    # Update global layout
                    global_layout = self.get_global_layout_state()
                    main_window._global_automate_layout = global_layout

                    # Apply to all other automate tabs (with broadcast=False to avoid recursion)
                    for i in range(main_window.tabs.count()):
                        widget = main_window.tabs.widget(i)
                        if widget and widget != self and hasattr(widget, 'apply_global_layout_state'):
                            widget.apply_global_layout_state(global_layout, broadcast=False)



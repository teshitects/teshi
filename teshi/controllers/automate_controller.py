import os
import uuid
import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QObject, Signal, QThread

from teshi.models.jupyter_node_model import JupyterNodeModel
from teshi.utils.yaml_graph_util import save_graph_to_yaml, load_graph_from_yaml
from teshi.utils import graph_util
from teshi.services.node_registry_service import NodeRegistryService
from teshi.utils.graph_execute_controller import GraphExecuteController
from teshi.utils.logger import get_logger

class AutomateController(QObject):
    """
    Business logic controller for Automate module.
    Manages graph state, file I/O, and execution.
    Separated from UI (AutomateModeWidget) to allow independent testing/CLI.
    """
    
    # Signals to notify UI of state changes
    graph_loaded = Signal() # Emitted when a project is loaded
    node_added = Signal(JupyterNodeModel) # Emitted when a new node is added
    node_removed = Signal(str) # Emitted when a node is removed (uuid)
    node_updated = Signal(JupyterNodeModel) # Emitted when node data changes
    execution_status_changed = Signal(str, str) # msg_id, status_str
    execution_binding = Signal(str) # binding_str
    log_message = Signal(str) # General log messages

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.notebook_dir = str(Path(file_path).parent.resolve())
        self.tab_id = str(uuid.uuid1())
        self.logger = get_logger()

        # Data State
        self.nodes: Dict[str, JupyterNodeModel] = {} # Key: uuid (or title? original used title as key in some places, but uuid is better) 
        # Note: Original implementation heavily relied on Title as key for graph structure. 
        # To maintain compatibility with existing files/format, we might need to keep using Title for implementation details
        # but try to shift to UUID where possible. 
        # For now, let's keep the model objects which have both.
        
        # Execution State
        self.thread: Optional[QThread] = None
        self.worker: Optional[GraphExecuteController] = None
        
        # Services
        self._init_node_registry()

    def _init_node_registry(self):
        project_root = self.notebook_dir
        while project_root and project_root != str(Path(project_root).parent):
            if os.path.exists(os.path.join(project_root, '.teshi')):
                break
            project_root = str(Path(project_root).parent)
        self.node_registry = NodeRegistryService(project_root)

    def load_project(self):
        """Load the project data from yaml files."""
        # 1. Load YAML data
        yaml_path = str(Path(self.file_path).with_suffix('.yaml'))
        yaml_graph_data = load_graph_from_yaml(yaml_path)
        
        # 2. Build consolidated internal state
        # Helper to index YAML nodes by Title
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

        # Clear current nodes
        self.nodes = {}
        
        # Apply Metadata to Nodes
        for title, yaml_item in yaml_items_data.items():
            # Create node model
            node = JupyterNodeModel(title, '')
            node.tab_id = self.tab_id
            
            node.x = yaml_item.get('x', 0)
            node.y = yaml_item.get('y', 0)
            node.params = yaml_item.get('params', {})
            node.node_type = yaml_item.get('node_type', '')
            node.uuid = yaml_item.get('uuid', str(uuid.uuid4()))
            
            # Now we have the UUID, we can use it as key
            self.nodes[node.uuid] = node
            
            # Load code from registry if needed
            if node.node_type:
                registry_data = self.node_registry.get_node_data(node.node_type)
                if registry_data:
                    node.code = registry_data['code']
        
        # Build connections from YAML
        for connection in yaml_graph_data.get('connections', []):
            from_title = connection.get('from', '')
            to_title = connection.get('to', '')
            if from_title and to_title:
                for node in self.nodes.values():
                    if node.title == from_title:
                        if to_title not in node.children:
                            node.children.append(to_title)
                        break
                
        # Emit Loaded Signal
        self.graph_loaded.emit()

    def save_project(self):
        """Save state to YAML."""
        self._sync_to_yaml()

    def _sync_to_yaml(self):
        yaml_path = str(Path(self.file_path).with_suffix('.yaml'))
        
        nodes_data = []
        connections_data = []
        
        for node in self.nodes.values():
            node_data = {
                "id": node.uuid,
                "title": node.title,
                "node_type": node.node_type,
                "pos": [node.x, node.y],
                "params": node.params
            }
            nodes_data.append(node_data)
            
            # Register node
            if node.code:
                self.node_registry.register_node(node.title, node.code)
                
            # Connections
            # Model stores children as list of titles. 
            # We need to ensure we export "from -> to" based on this children list.
            for child_title in node.children:
                if child_title in self.nodes:
                     connections_data.append({
                         "from": node.title,
                         "to": child_title
                     })

        graph_data = {
            "nodes": nodes_data,
            "connections": connections_data
        }
        
        try:
            save_graph_to_yaml(graph_data, yaml_path)
        except Exception as e:
            self.logger.error(f"Failed to sync to YAML: {e}")

    def add_node(self, title: str, code: str, pos=(0,0), params: dict = None):
        # Check if title already exists (titles must be unique for graph structure)
        if any(node.title == title for node in self.nodes.values()):
            self.logger.warning(f"Node with title {title} already exists.")
            return

        node = JupyterNodeModel(title, code)
        node.tab_id = self.tab_id
        node.x, node.y = pos
        node.uuid = str(uuid.uuid4())
        if params:
            node.params = params
        
        self.nodes[node.uuid] = node
        self.node_added.emit(node)
        self.save_project()

    def remove_node(self, uuid: str):
        node = self.nodes.get(uuid)
        if not node: return
        
        # Remove connections where this node is child (source -> this)
        title = node.title
        for other in self.nodes.values():
            if title in other.children:
                other.children.remove(title)
        
        # Remove from nodes
        del self.nodes[uuid]
            
        self.node_removed.emit(uuid)
        self.save_project()

    def update_node_code(self, uuid: str, new_code: str):
        node = self._get_node_by_uuid(uuid)
        if not node: return
        
        node.code = new_code
        node.code_changed = True
        
        # Check Title Change
        new_title = new_code.split('\n')[0]
        if new_title != node.title:
            self.rename_node(node, new_title)
        
        # Update Registry
        node_type = self.node_registry.register_node(node.title, node.code)
        node.node_type = node_type
        
        self.node_updated.emit(node)
        self.save_project()

    def rename_node(self, node: JupyterNodeModel, new_title: str):
        old_title = node.title
        
        # Update references in other nodes' children
        for other_node in self.nodes.values():
            if old_title in other_node.children:
                other_node.children.remove(old_title)
                other_node.children.append(new_title)
        
        node.title = new_title

    def update_node_params(self, uuid: str, params: dict):
        node = self._get_node_by_uuid(uuid)
        if not node: return
        node.params = params
        self.node_updated.emit(node)
        # self.save_project() # Optional auto-save on param change

    def update_node_position(self, uuid: str, x: float, y: float):
        node = self._get_node_by_uuid(uuid)
        if not node: return
        node.x = x
        node.y = y
        # We don't emit update for position to avoid spamming, or maybe we do depending on UI needs.
        # But definitely save continuously or on release?
        # Controller typically saves on explicit request or robust events. 
        # For drag drop, UI might call this controller method, then save later.

    def add_connection(self, from_uuid: str, to_uuid: str):
        source = self._get_node_by_uuid(from_uuid)
        target = self._get_node_by_uuid(to_uuid)
        if source and target:
            if target.title not in source.children:
                source.children.append(target.title)
                self.save_project()

    def remove_connection(self, from_uuid: str, to_uuid: str):
        source = self._get_node_by_uuid(from_uuid)
        target = self._get_node_by_uuid(to_uuid)
        if source and target:
             if target.title in source.children:
                 source.children.remove(target.title)
                 self.save_project()

    def _get_node_by_uuid(self, uuid: str) -> Optional[JupyterNodeModel]:
        for node in self.nodes.values():
            if node.uuid == uuid:
                return node
        return None

    def run_all(self):
        self.save_project()
        
        # Build strict dicts for Executor (it expects specific formats)
        # Graph: {title: [children_titles]}
        graph = {node.title: node.children for node in self.nodes.values()}
        # Nodes Data: {title: [code, uuid, params]}
        nodes_data = {node.title: [node.code, node.uuid, node.params] for node in self.nodes.values()}
        
        self._start_execution(graph, nodes_data)

    def run_single(self, uuid: str):
        self.save_project()
        
        target_node = self._get_node_by_uuid(uuid)
        if not target_node: return

        graph = {node.title: node.children for node in self.nodes.values()}
        nodes_data = {node.title: [node.code, node.uuid, node.params] for node in self.nodes.values()}
        
        self._start_execution(graph, nodes_data, single_node_title=target_node.title)

    def _start_execution(self, graph, nodes_data, single_node_title=None):
        if self.thread is not None:
             self.thread.quit()
             self.thread.wait()
             
        self.thread = QThread()
        self.worker = GraphExecuteController(graph, nodes_data, self.notebook_dir, self.tab_id, single_node_title)
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.worker.executor_process.connect(self._on_executor_process)
        self.worker.executor_binding.connect(self.execution_binding)
        
        if single_node_title:
            self.thread.started.connect(self.worker.execute_single_node_and_its_parents)
        else:
            self.thread.started.connect(self.worker.execute_all)
            
        self.thread.start()

    def _on_executor_process(self, process_str):
        # Relay to UI via sanitized signal
        # process_str format: msg_id:tab_id:status_info OR parent_msg_id#tab_id:status_info
        
        # We can parse it here or just relay.
        # Let's relay raw for now, or match verify tab_id?
        # The executor controller was initialized with our tab_id, so it should be fine.
        
        # Ideally, we parse "status:busy", "error:...", etc. and update our internal model state too.
        
        if "#" in process_str:
            first_part = process_str.split(":")[0]
            if "#" in first_part:
                msg_id, t_id = first_part.split("#")
                if t_id == self.tab_id:
                     status_info = process_str[len(first_part)+1:]
                     self.execution_status_changed.emit(msg_id, status_info)

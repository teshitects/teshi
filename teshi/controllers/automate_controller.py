import os
import uuid
import datetime
from pathlib import Path
from typing import Dict, List, Optional
from PySide6.QtCore import QObject, Signal, QThread

from teshi.models.nodes.base_node import BaseNode
from teshi.services.node_factory import NodeFactory
from teshi.utils.ipynb_file_util import load_notebook, save_notebook, add_cell, remove_cell
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
    node_added = Signal(BaseNode) # Emitted when a new node is added
    node_removed = Signal(str) # Emitted when a node is removed (uuid)
    node_updated = Signal(BaseNode) # Emitted when node data changes
    execution_status_changed = Signal(str, str) # msg_id, status_str
    execution_binding = Signal(str) # binding_str
    log_message = Signal(str) # General log messages

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.notebook_path = str(Path(file_path).with_suffix('.ipynb'))
        self.notebook_dir = str(Path(file_path).parent.resolve())
        self.tab_id = str(uuid.uuid1())
        self.logger = get_logger()

        # Data State
        self.nodes: Dict[str, BaseNode] = {} # Key: uuid
        
        self.notebook = None
        
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
        """Load the project data from ipynb and yaml files."""
        # 1. Ensure notebook exists
        self._ensure_notebook_exists()
        
        # 2. Load notebook
        self.notebook = load_notebook(self.notebook_path)
        
        # 3. Load YAML data
        yaml_path = str(Path(self.file_path).with_suffix('.yaml'))
        yaml_graph_data = load_graph_from_yaml(yaml_path)
        
        # 4. Load Metadata from Notebook (Legacy)
        ipynb_items_data = self.notebook.metadata.get("scene_data", {})
        
        # 5. Build consolidated internal state
        # Helper to index YAML nodes by Title
        yaml_items_data = {}
        for node_info in yaml_graph_data.get('nodes', []):
            title = node_info.get('title', '')
            if title:
                yaml_items_data[title] = {
                    'x': node_info.get('pos', [0, 0])[0], 
                    'y': node_info.get('pos', [0, 0])[1],
                    'params': node_info.get('params', {}),
                    'node_type': node_info.get('node_type', 'raw'), # Default to raw if missing
                    'uuid': node_info.get('id', '')
                }

        # Clear current nodes
        self.nodes = {}
        
        # Parse Notebook Cells -> Nodes
        # In legacy, everything was a cell. In new system, nodes generate cells.
        # We need to reconcile. If a cell exists, it corresponds to a node.
        # If that node doesn't have YAML metadata, we treat it as a Raw Node.
        
        cell_sources = {} # title -> source
        for cell in self.notebook.cells:
            if cell.cell_type == 'code':
                title = cell.source.split('\n')[0]
                cell_sources[title] = cell.source
        
        # If we have YAML data, we prioritize it to create nodes
        processed_titles = set()
        
        for title, y_data in yaml_items_data.items():
            processed_titles.add(title)
            code = cell_sources.get(title, "")
            
            node = NodeFactory.create_node(
                node_type=y_data['node_type'],
                title=title,
                pos=(y_data['x'], y_data['y']),
                params=y_data['params'],
                node_uuid=y_data['uuid'],
                code=code # Used only for Raw nodes or if we want to restore exact code
            )
            node.tab_id = self.tab_id
            
            # Legacy children handling
            # Check ipynb metadata first as legacy
            ipynb_item = ipynb_items_data.get(title, {})
            node.children = ipynb_item.get('children', [])
            
            # We don't have explicit children in YAML nodes list usually, 
            # we rely on the connections list in YAML (not loaded here yet) or internal logic.
            # But the original code trusted ipynb children mostly.
            
            self.nodes[node.uuid] = node

        # Handle cells that are not in YAML (Legacy manual cells?)
        # Treat them as Raw Nodes
        for title, source in cell_sources.items():
            if title not in processed_titles:
                node = NodeFactory.create_node(
                    node_type="raw",
                    title=title,
                    code=source,
                    params={},
                    node_uuid=str(uuid.uuid4())
                )
                node.tab_id = self.tab_id
                
                # Check legacy metadata
                ipynb_item = ipynb_items_data.get(title, {})
                node.x = ipynb_item.get('x', 0)
                node.y = ipynb_item.get('y', 0)
                node.children = ipynb_item.get('children', [])
                node.uuid = ipynb_item.get('uuid', node.uuid) # Use existing UUID if available
                
                self.nodes[node.uuid] = node
                
        # Load connections from YAML if available and authoritative?
        # The original code preferred IPynb metadata for connections. 
        # "Connections (Children) come from IPynb metadata usually, or YAML"
        # We'll stick to what we loaded into node.children above.

        # Emit Loaded Signal
        self.graph_loaded.emit()

    def _ensure_notebook_exists(self):
        if not Path(self.notebook_path).exists():
            import nbformat
            nb = nbformat.v4.new_notebook()
            with open(self.notebook_path, 'w', encoding='utf-8') as f:
                nbformat.write(nb, f)

    def save_project(self):
        """Save state to notebook and YAML."""
        if not self.notebook:
            return

        # 1. Sync Logic (Nodes to Notebook Cells)
        current_titles = [cell.source.split('\n')[0] for cell in self.notebook.cells if cell.cell_type == 'code']
        node_titles = [node.title for node in self.nodes.values()]
        
        # A. Add new nodes
        for node in self.nodes.values():
            if node.title not in current_titles:
                add_cell(self.notebook, node.code)
        
        # B. Remove deleted nodes
        # We need to iterate backwards to remove safely
        for i in range(len(self.notebook.cells) - 1, -1, -1):
            cell = self.notebook.cells[i]
            if cell.cell_type == 'code':
                title = cell.source.split('\n')[0]
                if title not in node_titles:
                    remove_cell(self.notebook, i)

        # C. Update code content
        for cell in self.notebook.cells:
            if cell.cell_type == 'code':
                title = cell.source.split('\n')[0]
                # Find node by title (since notebook only has titles)
                node = next((n for n in self.nodes.values() if n.title == title), None)
                if node:
                    if node.code != cell.source:
                        cell.source = node.code

        # D. Update Metadata (IPynb)
        items_data = {node.title: node.to_dict() for node in self.nodes.values()}
        self.notebook.metadata["scene_data"] = items_data
        self.notebook.metadata["last_modified"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.notebook.metadata["last_modified_by"] = "Teshi Automate"
        
        save_notebook(self.notebook, self.notebook_path)

        # E. Sync to YAML
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

    def add_node(self, title: str, code: str, pos=(0,0), params: dict = None, node_type: str = "raw"):
        # Check if title already exists (titles must be unique for graph structure)
        if any(node.title == title for node in self.nodes.values()):
            self.logger.warning(f"Node with title {title} already exists.")
            return

        node = NodeFactory.create_node(node_type, title, pos, params, code=code)
        node.tab_id = self.tab_id
        
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

    def rename_node(self, node: BaseNode, new_title: str):
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

    def _get_node_by_uuid(self, uuid: str) -> Optional[BaseNode]:
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

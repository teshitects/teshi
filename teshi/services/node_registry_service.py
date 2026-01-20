import os
import yaml
import hashlib
from typing import Dict, List, Optional
from pathlib import Path

class NodeRegistryService:
    """
    Node Registry Service - Manages node types and their corresponding code.
    Ensures that common node code is stored centrally rather than duplicated in setiap test case.
    """
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.registry_dir = os.path.join(project_path, '.teshi')
        self.registry_file = os.path.join(self.registry_dir, 'node_registry.yaml')
        self._nodes: Dict[str, Dict] = {}
        self._load_registry()

    def _load_registry(self):
        """Loads the registry from the YAML file."""
        if not os.path.exists(self.registry_file):
            os.makedirs(self.registry_dir, exist_ok=True)
            self._nodes = {}
            self._save_registry()
            return

        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self._nodes = data.get('nodes', {}) if data else {}
        except Exception as e:
            print(f"Error loading node registry: {e}")
            self._nodes = {}

    def _save_registry(self):
        """Saves the registry to the YAML file."""
        os.makedirs(self.registry_dir, exist_ok=True)
        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                yaml.safe_dump({'nodes': self._nodes}, f, allow_unicode=True)
        except Exception as e:
            print(f"Error saving node registry: {e}")

    def get_node_type(self, title: str, code: Optional[str] = None) -> str:
        """
        Extracts or generates a node type identifier from title/code.
        If title starts with '#', we use that as the primary identifier.
        """
        clean_title = title.strip()
        if clean_title.startswith('#'):
            # Use the title (slugified) as type
            node_type = clean_title.lstrip('#').strip().lower().replace(' ', '_')
            return node_type
        
        # Fallback to hash if no clear title
        if code:
            return hashlib.md5(code.encode()).hexdigest()[:12]
        return "unknown"

    def register_node(self, title: str, code: str) -> str:
        """
        Registers a node type in the registry.
        Returns the node_type identifier.
        """
        node_type = self.get_node_type(title, code)
        
        if node_type not in self._nodes or self._nodes[node_type]['code'] != code:
            self._nodes[node_type] = {
                'title': title,
                'code': code,
                'version': self._nodes.get(node_type, {}).get('version', 0) + 1
            }
            self._save_registry()
            
        return node_type

    def get_node_data(self, node_type: str) -> Optional[Dict]:
        """Returns node data (title, code) for a given node_type."""
        return self._nodes.get(node_type)

    def get_all_nodes(self) -> Dict[str, Dict]:
        """Returns all registered nodes."""
        return self._nodes

    def delete_node(self, node_type: str):
        """Removes a node from the registry."""
        if node_type in self._nodes:
            del self._nodes[node_type]
            self._save_registry()

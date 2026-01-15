import os
import yaml

class NodeLibManager:
    def __init__(self, library_path=None):
        if library_path:
            self.library_path = library_path
        else:
             # Default to user home .teshi directory
            self.library_path = os.path.join(os.path.expanduser("~"), ".teshi", "nodes.yaml")
        
        self.nodes = {}
        self.load_library()

    def load_library(self):
        if os.path.exists(self.library_path):
            with open(self.library_path, 'r', encoding='utf-8') as f:
                try:
                    self.nodes = yaml.safe_load(f) or {}
                except yaml.YAMLError as e:
                    print(f"Error loading node library: {e}")
                    self.nodes = {}
        else:
            self.nodes = {}

    def save_library(self):
        os.makedirs(os.path.dirname(self.library_path), exist_ok=True)
        with open(self.library_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self.nodes, f, allow_unicode=True)

    def get_node_code(self, title):
        return self.nodes.get(title, {}).get('code', "")

    def save_node_code(self, title, code):
        if title not in self.nodes:
            self.nodes[title] = {}
        self.nodes[title]['code'] = code
        self.save_library()

    def get_all_nodes(self):
        return self.nodes

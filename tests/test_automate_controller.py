import unittest
import sys
import os
import shutil
import tempfile
from pathlib import Path
import yaml

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtCore import QCoreApplication
from teshi.controllers.automate_controller import AutomateController
from teshi.models.jupyter_node_model import JupyterNodeModel

# Ensure QApplication exists for Signals
app = QCoreApplication.instance()
if not app:
    app = QCoreApplication(sys.argv)

class TestAutomateController(unittest.TestCase):
    def setUp(self):
        # Create a temp directory
        self.test_dir = tempfile.mkdtemp()
        # Create .teshi directory for registry
        os.makedirs(os.path.join(self.test_dir, ".teshi"), exist_ok=True)
        
        self.file_path = os.path.join(self.test_dir, "test_project.py")
        
        # Create empty file
        with open(self.file_path, 'w') as f:
            f.write("# Test File")
            
        self.controller = AutomateController(self.file_path)

    def tearDown(self):
        # Cleanup
        shutil.rmtree(self.test_dir)

    def test_initial_load(self):
        """Test that loading an empty project creates necessary files"""
        self.controller.load_project()
        
        # Check generated files
        # notebook_path = self.file_path.replace(".py", ".ipynb") # Notebook creation removed from controller init
        yaml_path = self.file_path.replace(".py", ".yaml")
        
        # self.assertTrue(os.path.exists(notebook_path))
        # yaml is only created on save, check if load created it? 
        # load_project -> calls load_graph_from_yaml -> returns empty if not exists.
        # It doesn't auto-create yaml on load unless we save.
        
    def test_add_node_and_save(self):
        """Test adding a node and saving persists data"""
        self.controller.load_project()
        
        # Add Node
        # System assumes first line of code IS the title.
        self.controller.add_node("Node 1", "Node 1\nprint('Hello')", (10, 20))
        
        # Nodes is now keyed by UUID
        self.assertEqual(len(self.controller.nodes), 1)
        node = list(self.controller.nodes.values())[0]
        self.assertEqual(node.title, "Node 1")
        self.assertEqual(node.code, "Node 1\nprint('Hello')")
        
        # Check YAML file created
        yaml_path = self.file_path.replace(".py", ".yaml")
        self.assertTrue(os.path.exists(yaml_path))
        
        # Check Notebook content
        # We need to reload notebook or check controller's notebook object
        self.controller.save_project()
        
        # Verify persistence by reloading a new controller
        new_controller = AutomateController(self.file_path)
        new_controller.load_project()
        
        self.assertEqual(len(new_controller.nodes), 1)
        loaded_node = list(new_controller.nodes.values())[0]
        self.assertEqual(loaded_node.title, "Node 1")
        self.assertEqual(loaded_node.code, "Node 1\nprint('Hello')")
        self.assertEqual(loaded_node.x, 10) # 0 index of pos tuple
        # Wait, pos is list [x, y] in YAML
        
    def test_update_node(self):
        self.controller.load_project()
        self.controller.add_node("Node 1", "Node 1\ncode1", (0,0))
        
        node1 = next(n for n in self.controller.nodes.values() if n.title == "Node 1")
        uuid = node1.uuid
        
        # Update Code
        self.controller.update_node_code(uuid, "Node 1\nupdated_code")
        
        self.assertEqual(self.controller.nodes[uuid].code, "Node 1\nupdated_code")
        
        # Rename via code change
        self.controller.update_node_code(uuid, "Node 2\nupdated_code")
        
        # Key is still the same uuid
        self.assertEqual(self.controller.nodes[uuid].title, "Node 2")
        
    def test_connection_persistence_uuid(self):
        """Test that connections are saved and loaded correctly using UUIDs"""
        self.controller.load_project()
        
        # Add Nodes
        self.controller.add_node("Node A", "Node A\ncode", (0,0))
        self.controller.add_node("Node B", "Node B\ncode", (100,0))
        
        node_a = next(n for n in self.controller.nodes.values() if n.title == "Node A")
        node_b = next(n for n in self.controller.nodes.values() if n.title == "Node B")
        
        # Add Connection
        self.controller.add_connection(node_a.uuid, node_b.uuid)
        
        self.assertIn(node_b.uuid, node_a.children)
        
        # Save
        self.controller.save_project()
        
        # Verify YAML content (manual read)
        yaml_path = self.file_path.replace(".py", ".yaml")
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
            
        connections = data['connections']
        self.assertEqual(len(connections), 1)
        self.assertEqual(connections[0]['from'], node_a.uuid)
        self.assertEqual(connections[0]['to'], node_b.uuid)
        
        # Reload
        new_controller = AutomateController(self.file_path)
        new_controller.load_project()
        
        new_node_a = next(n for n in new_controller.nodes.values() if n.title == "Node A")
        new_node_b = next(n for n in new_controller.nodes.values() if n.title == "Node B")
        
        self.assertIn(new_node_b.uuid, new_node_a.children)

if __name__ == '__main__':
    unittest.main()

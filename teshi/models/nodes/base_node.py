from abc import ABC, abstractmethod
import uuid

class BaseNode(ABC):
    """
    Abstract Base Class for all automation nodes.
    Common attributes: uuid, title, position, params, children links.
    """
    def __init__(self, title, pos=(0,0), params=None, node_uuid=None):
        self.title = title
        self.x = pos[0]
        self.y = pos[1]
        self.params = params or {}
        self.uuid = node_uuid or str(uuid.uuid4())
        
        # Graph structure
        self.children = [] # List of child titles
        
        # Execution State
        self.msg_id = ""
        self.tab_id = ""
        self.last_status = ""
        self.result = ""
        self.code_changed = False # Dirty flag for saving/syncing
        self.code = "" # The generated or raw code
        
        # Metadata
        self.node_type = "base"

    @abstractmethod
    def generate_code(self) -> str:
        """
        Generates the executable Python code for this node.
        Updates self.code and returns it.
        """
        pass

    def to_dict(self):
        """Serialization for YAML/Metadata"""
        return {
            "uuid": self.uuid,
            "title": self.title,
            "node_type": self.node_type,
            "pos": [self.x, self.y],
            "params": self.params,
            "children": self.children,
            # We don't necessarily save 'code' in metadata if it's generated, 
            # but for consistency with legacy, we might want to.
            # However, for generated nodes, 'code' is a derived property.
            "code": self.code 
        }

    def __str__(self):
        return f"{self.title} ({self.node_type})"

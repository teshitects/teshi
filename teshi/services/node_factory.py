from teshi.models.nodes.base_node import BaseNode
from teshi.models.nodes.raw_node import RawCodeNode
from teshi.models.nodes.api_node import APINode
from teshi.models.nodes.ui_node import UINode
from teshi.models.nodes.mobile_node import MobileUINode

class NodeFactory:
    """
    Factory for creating node instances based on type identifier.
    """
    
    @staticmethod
    def create_node(node_type: str, title: str, pos=(0,0), params=None, node_uuid=None, code="") -> BaseNode:
        """
        Creates and returns a specific Node instance.
        """
        params = params or {}
        
        if node_type == "api":
            node = APINode(title, pos, params, node_uuid)
            node.generate_code()
            return node
        elif node_type == "ui":
            node = UINode(title, pos, params, node_uuid)
            node.generate_code()
            return node
        elif node_type == "mobile_ui":
            node = MobileUINode(title, pos, params, node_uuid)
            node.generate_code()
            return node
        elif node_type == "raw":
            return RawCodeNode(title, code, pos, params, node_uuid)
        else:
            # Default fallback for legacy or unknown types is RawCodeNode
            # If code is provided, we use it.
            return RawCodeNode(title, code, pos, params, node_uuid)

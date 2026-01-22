from .base_node import BaseNode

class RawCodeNode(BaseNode):
    """
    Legacy-style node where the user manually inputs the raw python code.
    Identified by type 'raw' or empty type in legacy files.
    """
    def __init__(self, title, code="", pos=(0,0), params=None, node_uuid=None):
        super().__init__(title, pos, params, node_uuid)
        self.node_type = "raw"
        self.code = code

    def generate_code(self) -> str:
        """
        For Raw nodes, the code is what the user typed.
        We return it as-is.
        """
        return self.code

    def set_code(self, new_code: str):
        """
        Specific method for RawNode to update its manual code.
        """
        self.code = new_code

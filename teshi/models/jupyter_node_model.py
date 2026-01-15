class JupyterNodeModel(object):
    def __init__(self, title, code, parent=None):
        self.title = title
        self.code = code
        self.source = None
        self.destination = None
        self.children = []
        self.x = 0
        self.y = 0
        self.uuid = None
        self.msg_id = ""
        self.tab_id = ""
        self.last_status = ""
        self.result = ""
        self.code_changed = False
        super().__init__()

    def __str__(self):
        return self.title

    def to_dict(self):
        return {
            "title": self.title,
            "code": self.code,
            "source": self.source,
            "destination": self.destination,
            "children": self.children,
            "x": self.x,
            "y": self.y,
            "result": self.result,
            "uuid": self.uuid
            }
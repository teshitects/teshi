from PySide6.QtCore import QObject, Signal

class ItemSignals(QObject):
    # 定义自定义信号
    nodeClicked = Signal(dict)  # 携带节点ID参数
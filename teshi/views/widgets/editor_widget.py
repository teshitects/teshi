from PySide6.QtWidgets import QTextEdit, QMessageBox, QFrame
from PySide6.QtCore import Signal, QFileInfo, QEvent


class EditorWidget(QTextEdit):
    modifiedChanged = Signal(bool)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.filePath = file_path
        self.setFrameShape(QFrame.NoFrame)
        self.setLineWidth(0)

        self.load()

        self.document().modificationChanged.connect(self._on_modification_changed)

    @property
    def dirty(self) -> bool:
        return self.document().isModified()

    def _on_modification_changed(self, changed: bool):
        self.modifiedChanged.emit(changed)

    def load(self):
        try:
            with open(self.filePath, "r", encoding="utf-8") as f:
                text = f.read()
                self.setPlainText(text)
                self.document().setModified(False)
        except Exception as e:
            QMessageBox.warning(self, "Open error",
                                f"Cannot open {self.filePath}:\n{e}")

    def save(self) -> bool:
        try:
            with open(self.filePath, "w", encoding="utf-8") as f:
                f.write(self.toPlainText())

            self.document().setModified(False)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save error", f"Cannot save {self.filePath}:\n{e}")
            return False
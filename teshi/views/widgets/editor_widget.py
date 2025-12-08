from PySide6.QtWidgets import QTextEdit, QMessageBox, QFrame
from PySide6.QtCore import Signal, QFileInfo, QEvent

class EditorWidget(QTextEdit):
    modifiedChanged = Signal(bool)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.filePath = file_path
        self._dirty = False
        self.setFrameShape(QFrame.NoFrame)
        self.setLineWidth(0)


        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.setPlainText(f.read())
        except Exception as e:
            QMessageBox.warning(self, "Open error", f"Failed to open {file_path}:\n{e}")

        self.textChanged.connect(self._on_text_changed)
        self.load()

    @property
    def dirty(self) -> bool:
        return self._dirty

    @dirty.setter
    def dirty(self, value: bool):
        if self._dirty != value:
            self._dirty = value
            self.modifiedChanged.emit(value)

    def _on_text_changed(self):
        if not self._dirty:
            self.dirty = True

    def load(self):
        try:
            with open(self.filePath, "r", encoding="utf-8") as f:
                text = f.read()
                self.blockSignals(True)
                self.setPlainText(text)
                self.blockSignals(False)
        except Exception as e:
            QMessageBox.warning(self, "Open error",
                                f"Cannot open {self.filePath}:\n{e}")
        finally:
            self.dirty = False

    def save(self) -> bool:
        try:
            with open(self.filePath, "w", encoding="utf-8") as f:
                f.write(self.toPlainText())

            self.dirty = False
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save error", f"Cannot save {self.filePath}:\n{e}")
            return False

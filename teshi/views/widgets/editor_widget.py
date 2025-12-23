from PySide6.QtWidgets import QTextEdit, QMessageBox, QFrame, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QToolButton, QStackedWidget
from PySide6.QtCore import Signal, QFileInfo, QEvent, Qt
from PySide6.QtGui import QIcon, QAction

from teshi.utils.bdd_converter import BDDConverter
from teshi.views.widgets.bdd_view import BDDViewWidget


class EditorWidget(QWidget):
    modifiedChanged = Signal(bool)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.filePath = file_path
        self._is_bdd_mode = False
        self._global_bdd_mode = False
        self._original_content = ""
        self._pending_bdd_conversion = False  # Flag for deferred BDD conversion
        
        # Initialize BDD converter
        self.bdd_converter = BDDConverter()
        
        self._setup_ui()
        self.load()

        self.text_edit.document().modificationChanged.connect(self._on_modification_changed)

    def _setup_ui(self):
        """Setup the UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create toolbar for BDD toggle
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 2, 5, 2)
        
        # BDD toggle button
        self.bdd_button = QPushButton("BDD")
        self.bdd_button.setMaximumWidth(60)
        self.bdd_button.setToolTip("Toggle BDD mode")
        self.bdd_button.clicked.connect(self._toggle_bdd_mode)
        
        toolbar_layout.addWidget(self.bdd_button)
        toolbar_layout.addStretch()
        
        # Add toolbar to layout
        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar_layout)
        toolbar_widget.setMaximumHeight(30)
        layout.addWidget(toolbar_widget)
        
        # Create stacked widget for switching between text editor and BDD view
        self.stacked_widget = QStackedWidget()
        
        # Text editor (raw content)
        self.text_edit = QTextEdit()
        self.text_edit.setFrameShape(QFrame.NoFrame)
        self.text_edit.setLineWidth(0)
        self.stacked_widget.addWidget(self.text_edit)
        
        # BDD view widget
        self.bdd_view = BDDViewWidget()
        self.stacked_widget.addWidget(self.bdd_view)
        
        layout.addWidget(self.stacked_widget)
    
    @property
    def dirty(self) -> bool:
        return self.text_edit.document().isModified()

    def _on_modification_changed(self, changed: bool):
        self.modifiedChanged.emit(changed)
    
    def _toggle_bdd_mode(self):
        """Toggle between standard and BDD format"""
        if self._is_bdd_mode:
            # Switch back to standard format
            self.stacked_widget.setCurrentWidget(self.text_edit)
            self._is_bdd_mode = False
            self.bdd_button.setText("BDD")
            self._pending_bdd_conversion = False
            
            # If global BDD mode is enabled, disable it
            if self._global_bdd_mode:
                # Find main window and disable global mode
                main_window = self.parent()
                while main_window and not hasattr(main_window, 'global_bdd_mode_changed'):
                    main_window = main_window.parent()
                
                if main_window and hasattr(main_window, '_toggle_global_bdd_mode'):
                    main_window._toggle_global_bdd_mode()
        else:
            # Switch to BDD format
            self._apply_bdd_mode()
            
            # If this is the first local BDD activation, trigger global mode
            if not self._global_bdd_mode:
                # Signal to main window to enable global BDD mode
                main_window = self.parent()
                while main_window and not hasattr(main_window, 'global_bdd_mode_changed'):
                    main_window = main_window.parent()
                
                if main_window and hasattr(main_window, '_toggle_global_bdd_mode'):
                    main_window._toggle_global_bdd_mode()
    
    def set_global_bdd_mode(self, enabled: bool, defer_conversion: bool = False):
        """Set global BDD mode state
        
        Args:
            enabled: Whether to enable BDD mode
            defer_conversion: If True, defer actual conversion until the tab is activated
        """
        self._global_bdd_mode = enabled
        
        if enabled and not self._is_bdd_mode:
            if defer_conversion:
                # Just mark that BDD mode should be enabled, don't convert yet
                # Conversion will happen when the tab becomes active
                self._pending_bdd_conversion = True
            else:
                # Enable BDD mode for this editor immediately
                self._apply_bdd_mode()
        elif not enabled and self._is_bdd_mode:
            # Disable BDD mode for this editor
            self.stacked_widget.setCurrentWidget(self.text_edit)
            self._is_bdd_mode = False
            self.bdd_button.setText("BDD")
            self._pending_bdd_conversion = False
    
    def _apply_bdd_mode(self):
        """Actually apply BDD mode conversion"""
        if self._is_bdd_mode:
            return  # Already in BDD mode
        
        self._original_content = self.text_edit.toPlainText()
        try:
            bdd_content = self.bdd_converter.convert_to_bdd(self._original_content)
            self.bdd_view.set_bdd_content(bdd_content)
            self.stacked_widget.setCurrentWidget(self.bdd_view)
            self._is_bdd_mode = True
            self.bdd_button.setText("Raw")
            self._pending_bdd_conversion = False
        except Exception as e:
            QMessageBox.warning(self, "Conversion Error", f"Failed to convert to BDD format:\n{e}")
            self._pending_bdd_conversion = False
    
    def activate_if_pending(self):
        """Activate pending BDD conversion if any"""
        if hasattr(self, '_pending_bdd_conversion') and self._pending_bdd_conversion:
            self._apply_bdd_mode()
    
    def toPlainText(self) -> str:
        """Get plain text from the editor"""
        return self.text_edit.toPlainText()
    
    def setPlainText(self, text: str):
        """Set plain text to the editor"""
        self.text_edit.setPlainText(text)
    
    def document(self):
        """Get the document"""
        return self.text_edit.document()

    def load(self):
        try:
            with open(self.filePath, "r", encoding="utf-8") as f:
                text = f.read()
                self.setPlainText(text)
                self.text_edit.document().setModified(False)
                self._original_content = text
        except Exception as e:
            QMessageBox.warning(self, "Open error",
                                f"Cannot open {self.filePath}:\n{e}")

    def save(self) -> bool:
        try:
            # Save in original format, not BDD format
            content_to_save = self._original_content if self._is_bdd_mode else self.toPlainText()
            
            with open(self.filePath, "w", encoding="utf-8") as f:
                f.write(content_to_save)

            self.text_edit.document().setModified(False)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save error", f"Cannot save {self.filePath}:\n{e}")
            return False
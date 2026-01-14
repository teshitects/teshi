from PySide6.QtWidgets import QTextEdit, QMessageBox, QFrame, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QToolButton, QStackedWidget
from PySide6.QtCore import Signal, QFileInfo, QEvent, Qt
from PySide6.QtGui import QIcon, QAction, QColor

from teshi.utils.bdd_converter import BDDConverter
from teshi.views.widgets.bdd_view import BDDViewWidget
from teshi.utils.keyword_highlighter import KeywordHighlighter


class EditorWidget(QWidget):
    modifiedChanged = Signal(bool)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.filePath = file_path
        self._is_bdd_mode = False
        self._global_bdd_mode = False
        self._original_content = ""
        self._pending_bdd_conversion = False  # Flag for deferred BDD conversion
        self._suppress_text_change = False  # Flag to suppress text change handling
        
        # Initialize BDD converter
        self.bdd_converter = BDDConverter()
        
        # Initialize keyword highlighter
        self.keyword_highlighter = KeywordHighlighter()
        
        self._setup_ui()
        self.load()

        self.text_edit.document().modificationChanged.connect(self._on_modification_changed)
        # Connect text change to reapply highlighting
        self.text_edit.textChanged.connect(self._on_text_changed)

    def _setup_ui(self):
        """Setup UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create toolbar for BDD toggle
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 2, 5, 2)
        
        # Button style sheet for active/inactive states
        self.active_btn_style = "background-color: #0078d4; color: white; border-radius: 4px; font-weight: bold;"
        self.inactive_btn_style = "background-color: transparent; border: 1px solid #ccc; border-radius: 4px;"

        # RAW button
        self.raw_btn = QPushButton("RAW")
        self.raw_btn.setFixedWidth(60)
        self.raw_btn.setToolTip("Switch to Raw text mode")
        self.raw_btn.clicked.connect(self._on_raw_clicked)
        
        # BDD button
        self.bdd_btn = QPushButton("BDD")
        self.bdd_btn.setFixedWidth(60)
        self.bdd_btn.setToolTip("Switch to BDD mode")
        self.bdd_btn.clicked.connect(self._on_bdd_clicked)
        
        toolbar_layout.addWidget(self.raw_btn)
        toolbar_layout.addWidget(self.bdd_btn)
        toolbar_layout.addStretch()
        
        # Initial button states
        self._update_button_states()
        
        # Add toolbar to layout
        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar_layout)
        toolbar_widget.setMaximumHeight(35)
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
    
    def _on_text_changed(self):
        """Handle text change - reapply highlighting in text mode"""
        # Check if this is a system-initiated change (not user input)
        if hasattr(self, '_suppress_text_change') and self._suppress_text_change:
            print(f"[EDITOR] _on_text_changed for {self.filePath} - SUPPRESSED (system-initiated)")
            return
            
        if not self._is_bdd_mode and self.keyword_highlighter.keywords:
            # Use a timer to avoid performance issues during typing
            if not hasattr(self, '_highlight_timer'):
                from PySide6.QtCore import QTimer
                self._highlight_timer = QTimer()
                self._highlight_timer.setSingleShot(True)
                self._highlight_timer.timeout.connect(self._delayed_highlight)
            
            print(f"[EDITOR] _on_text_changed for {self.filePath}, starting highlight timer")
            self._highlight_timer.start(300)  # 300ms delay
    
    def _delayed_highlight(self):
        """Apply highlighting after delay"""
        if not self._is_bdd_mode:
            print(f"[EDITOR] _delayed_highlight for {self.filePath}")
            self._suppress_text_change = True
            try:
                self._apply_highlighting()
            finally:
                self._suppress_text_change = False
    
    def closeEvent(self, event):
        """Clean up resources when widget is closed"""
        # Clean up highlight timer
        if hasattr(self, '_highlight_timer'):
            self._highlight_timer.stop()
            self._highlight_timer.deleteLater()
            delattr(self, '_highlight_timer')
        
        # Clean up highlighter
        if hasattr(self, 'highlighter'):
            self.highlighter.setDocument(None)
            self.highlighter.deleteLater()
            self.highlighter = None
        
        super().closeEvent(event)
    
    def __del__(self):
        """Destructor to ensure resource cleanup"""
        try:
            # Clean up highlighter if not already cleaned
            if hasattr(self, 'highlighter') and self.highlighter:
                self.highlighter.setDocument(None)
                self.highlighter = None
        except:
            pass
    
    def _update_button_states(self):
        """Update button styles based on current mode"""
        if self._is_bdd_mode:
            self.bdd_btn.setStyleSheet(self.active_btn_style)
            self.raw_btn.setStyleSheet(self.inactive_btn_style)
        else:
            self.raw_btn.setStyleSheet(self.active_btn_style)
            self.bdd_btn.setStyleSheet(self.inactive_btn_style)

    def _on_raw_clicked(self):
        """Switch to RAW mode"""
        if not self._is_bdd_mode:
            return
        self._toggle_bdd_mode()

    def _on_bdd_clicked(self):
        """Switch to BDD mode"""
        if self._is_bdd_mode:
            return
        self._toggle_bdd_mode()

    def _toggle_bdd_mode(self):
        """Toggle between standard and BDD format"""
        if self._is_bdd_mode:
            # Switch back to standard format
            self.stacked_widget.setCurrentWidget(self.text_edit)
            self._is_bdd_mode = False
            self._update_button_states()
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
            
            # If this is first local BDD activation, trigger global mode
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
            self._update_button_states()
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
            self._update_button_states()
            self._pending_bdd_conversion = False
            
            # Apply keyword highlighting after switching to BDD mode
            self._apply_highlighting()
        except Exception as e:
            QMessageBox.warning(self, "Conversion Error", f"Failed to convert to BDD format:\\n{e}")
            self._pending_bdd_conversion = False
    
    def activate_if_pending(self):
        """Activate pending BDD conversion if any"""
        if hasattr(self, '_pending_bdd_conversion') and self._pending_bdd_conversion:
            self._apply_bdd_mode()
    
    def toPlainText(self) -> str:
        """Get plain text from editor"""
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
                                f"Cannot open {self.filePath}:\\n{e}")

    def save(self) -> bool:
        try:
            # Save in original format, not BDD format
            content_to_save = self._original_content if self._is_bdd_mode else self.toPlainText()
            
            with open(self.filePath, "w", encoding="utf-8") as f:
                f.write(content_to_save)

            self.text_edit.document().setModified(False)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save error", f"Cannot save {self.filePath}:\\n{e}")
            return False
    
    # Keyword highlighting methods
    def set_highlight_keywords(self, keywords: list):
        """Set keywords to highlight"""
        self.keyword_highlighter.set_keywords(keywords)
        self._suppress_text_change = True
        try:
            self._apply_highlighting()
        finally:
            self._suppress_text_change = False
    
    def add_highlight_keyword(self, keyword: str):
        """Add single keyword to highlight"""
        self.keyword_highlighter.add_keyword(keyword)
        self._suppress_text_change = True
        try:
            self._apply_highlighting()
        finally:
            self._suppress_text_change = False
    
    def remove_highlight_keyword(self, keyword: str):
        """Clear single keyword from highlight"""
        self.keyword_highlighter.remove_keyword(keyword)
        self._suppress_text_change = True
        try:
            self._apply_highlighting()
        finally:
            self._suppress_text_change = False
    
    def clear_highlight_keywords(self):
        """Clear all highlight keywords"""
        self.keyword_highlighter.clear_keywords()
        self._suppress_text_change = True
        try:
            self._apply_highlighting()
        finally:
            self._suppress_text_change = False
    
    def set_highlight_color(self, color: QColor):
        """Set highlight color"""
        self.keyword_highlighter.set_highlight_color(color)
        self._suppress_text_change = True
        try:
            self._apply_highlighting()
        finally:
            self._suppress_text_change = False
    
    def get_highlight_keywords(self) -> list:
        """Get current highlight keywords"""
        return self.keyword_highlighter.keywords.copy()
    
    def _apply_highlighting(self):
        """Highlight content based on current mode"""
        if self._is_bdd_mode:
            # 在BDD模式下，高亮BDD内容
            self._apply_bdd_highlighting()
        else:
            # In text mode, highlight text edit content
            self.keyword_highlighter.highlight_text(self.text_edit)
    
    def _apply_bdd_highlighting(self):
        """在BDD视图中应用关键字高亮"""
        if not hasattr(self, 'bdd_view') or not self.keyword_highlighter.keywords:
            return
        
        # Get current BDD content
        try:
            current_content = self.bdd_converter.convert_to_bdd(self._original_content)
            highlighted_content = self.keyword_highlighter.highlight_html_content(current_content)
            print(f"[EDITOR] Applying BDD highlighting for {self.filePath}")
            self.bdd_view.set_bdd_content(highlighted_content)
        except Exception as e:
            print(f"Error applying BDD highlighting: {e}")
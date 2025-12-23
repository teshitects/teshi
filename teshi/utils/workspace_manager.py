import os
import json
import time
from typing import Dict, List, Any
from PySide6.QtCore import QObject, QTimer, Qt


class WorkspaceManager(QObject):
    """Workspace manager, responsible for auto-saving and restoring workspace state"""
    
    def __init__(self, project_path: str, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.teshi_dir = os.path.join(project_path, '.teshi')
        self.workspace_file = os.path.join(self.teshi_dir, 'workspace.json')
        self.main_window = None
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._save_workspace)
        self.save_delay = 2000  # Save after 2 seconds
        
        # Ensure .teshi directory exists
        os.makedirs(self.teshi_dir, exist_ok=True)
    
    def set_main_window(self, main_window):
        """Set main window reference"""
        self.main_window = main_window
    
    def trigger_save(self):
        """Trigger delayed save"""
        self.save_timer.stop()
        self.save_timer.start(self.save_delay)
    
    def get_workspace_state(self, main_window) -> Dict[str, Any]:
        """Get current workspace state"""
        workspace_data = {
            'timestamp': time.time(),
            'window_state': {
                'maximized': main_window.isMaximized()
            },
            'open_tabs': [],
            'current_tab_index': main_window.tabs.currentIndex() if hasattr(main_window, 'tabs') else -1,
            'dock_states': {}
        }
        
        # Save open tabs
        if hasattr(main_window, 'tabs'):
            for i in range(main_window.tabs.count()):
                widget = main_window.tabs.widget(i)
                if hasattr(widget, 'filePath'):
                    workspace_data['open_tabs'].append({
                        'file_path': widget.filePath,
                        'is_dirty': widget.dirty if hasattr(widget, 'dirty') else False
                    })
        
        # Save dock widget states
        print(f"DEBUG: Checking main_window attributes...")
        print(f"DEBUG: main_window has project_dock: {hasattr(main_window, 'project_dock')}")
        print(f"DEBUG: main_window has explorer: {hasattr(main_window, 'explorer')}")
        if hasattr(main_window, 'project_dock'):
            workspace_data['dock_states']['project'] = {
                'visible': main_window.project_dock.isVisible(),
                'width': main_window.project_dock.width()
            }
            
            # Save project explorer expanded state
            if hasattr(main_window, 'explorer'):
                expanded_folders = main_window.explorer.get_expanded_state()
                print(f"DEBUG: Found {len(expanded_folders)} expanded folders: {expanded_folders}")
                workspace_data['project_explorer'] = {
                    'expanded_folders': expanded_folders
                }
                print(f"DEBUG: project_explorer state saved!")
            else:
                print(f"DEBUG: main_window does NOT have explorer attribute!")
        else:
            print(f"DEBUG: main_window does NOT have project_dock attribute!")
        
        # Save BDD Mind Map dock state
        if hasattr(main_window, 'bdd_mind_map_dock'):
            workspace_data['dock_states']['bdd_mind_map'] = {
                'visible': main_window.bdd_mind_map_dock.isVisible(),
                'width': main_window.bdd_mind_map_dock.width()
            }
        
        # Save global BDD mode
        if hasattr(main_window, '_global_bdd_mode'):
            workspace_data['bdd_mode'] = main_window._global_bdd_mode
        
        return workspace_data
    
    def save_workspace(self, main_window):
        """Save workspace immediately"""
        try:
            # Simplified and fast workspace data collection
            workspace_data = {
                'timestamp': time.time(),
                'window_state': {
                    'maximized': main_window.isMaximized()
                },
                'open_tabs': [],
                'current_tab_index': getattr(main_window.tabs, 'currentIndex', lambda: -1)() if hasattr(main_window, 'tabs') else -1,
                'dock_states': {}
            }
            
            # Fast tab collection with minimal attribute access
            if hasattr(main_window, 'tabs'):
                try:
                    for i in range(main_window.tabs.count()):
                        widget = main_window.tabs.widget(i)
                        if widget and hasattr(widget, 'filePath'):
                            workspace_data['open_tabs'].append({
                                'file_path': widget.filePath,
                                'is_dirty': getattr(widget, 'dirty', False)
                            })
                except:
                    # If tab collection fails, skip it
                    pass
            
            # Simple dock state
            if hasattr(main_window, 'project_dock'):
                try:
                    workspace_data['dock_states']['project'] = {
                        'visible': main_window.project_dock.isVisible(),
                        'width': main_window.project_dock.width()
                    }
                    
                    # Save project explorer expanded state
                    if hasattr(main_window, 'explorer'):
                        expanded_folders = main_window.explorer.get_expanded_state()
                        workspace_data['project_explorer'] = {
                            'expanded_folders': expanded_folders
                        }
                except:
                    pass
            
            # Save BDD Mind Map dock state
            if hasattr(main_window, 'bdd_mind_map_dock'):
                try:
                    workspace_data['dock_states']['bdd_mind_map'] = {
                        'visible': main_window.bdd_mind_map_dock.isVisible(),
                        'width': main_window.bdd_mind_map_dock.width()
                    }
                except:
                    pass
            
            # Save global BDD mode
            if hasattr(main_window, '_global_bdd_mode'):
                try:
                    workspace_data['bdd_mode'] = main_window._global_bdd_mode
                except:
                    pass
            
            # Fast JSON write without pretty printing for speed
            with open(self.workspace_file, 'w', encoding='utf-8') as f:
                json.dump(workspace_data, f, separators=(',', ':'), ensure_ascii=False)
            print(f"Workspace saved to: {self.workspace_file}")
        except Exception as e:
            print(f"Failed to save workspace: {e}")
    
    def _save_workspace(self):
        """Save method triggered by timer"""
        if self.main_window:
            self.save_workspace(self.main_window)
    
    def load_workspace(self) -> Dict[str, Any]:
        """Load workspace state"""
        if not os.path.exists(self.workspace_file):
            return {}
        
        try:
            with open(self.workspace_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load workspace: {e}")
            return {}
    
    def restore_workspace(self, main_window):
        """Restore workspace state"""
        workspace_data = self.load_workspace()
        if not workspace_data:
            return
        
        # Restore window state (only maximized status)
        window_state = workspace_data.get('window_state', {})
        if window_state:
            if window_state.get('maximized', False):
                main_window.showMaximized()
            else:
                # Center window when not maximized
                screen = main_window.screen()
                if screen:
                    screen_geometry = screen.availableGeometry()
                    window_width = 1200
                    window_height = 800
                    x = (screen_geometry.width() - window_width) // 2
                    y = (screen_geometry.height() - window_height) // 2
                    main_window.setGeometry(x, y, window_width, window_height)
        
        # Restore dock widget states
        dock_states = workspace_data.get('dock_states', {})
        
        # Restore project dock
        project_width = None
        if hasattr(main_window, 'project_dock') and 'project' in dock_states:
            project_state = dock_states['project']
            # Handle both old format (boolean) and new format (dict)
            if isinstance(project_state, bool):
                if project_state:
                    main_window.project_dock.show()
                else:
                    main_window.project_dock.hide()
            else:
                # New format with width
                if project_state.get('visible', False):
                    main_window.project_dock.show()
                else:
                    main_window.project_dock.hide()
                
                # Save width for later restoration
                project_width = project_state.get('width')
        
        # Restore BDD Mind Map dock
        bdd_width = None
        if hasattr(main_window, 'bdd_mind_map_dock') and 'bdd_mind_map' in dock_states:
            bdd_state = dock_states['bdd_mind_map']
            if bdd_state.get('visible', False):
                main_window.bdd_mind_map_dock.show()
            else:
                main_window.bdd_mind_map_dock.hide()
            
            # Save width for later restoration
            bdd_width = bdd_state.get('width')
        
        # Use QTimer to restore dock widths after the window is fully initialized
        from PySide6.QtCore import QTimer
        def restore_dock_widths():
            if project_width and project_width > 0 and hasattr(main_window, 'project_dock'):
                main_window.resizeDocks([main_window.project_dock], [project_width], Qt.Horizontal)
            if bdd_width and bdd_width > 0 and hasattr(main_window, 'bdd_mind_map_dock'):
                main_window.resizeDocks([main_window.bdd_mind_map_dock], [bdd_width], Qt.Horizontal)
        
        QTimer.singleShot(100, restore_dock_widths)
        
        # Restore BDD mode
        bdd_mode = workspace_data.get('bdd_mode', False)
        if bdd_mode and hasattr(main_window, '_global_bdd_mode'):
            main_window._global_bdd_mode = bdd_mode
            # Apply to all tabs will be done after tabs are restored
        
        # Restore project explorer state
        project_explorer = workspace_data.get('project_explorer', {})
        if project_explorer and hasattr(main_window, 'explorer'):
            expanded_folders = project_explorer.get('expanded_folders', [])
            # Use QTimer to delay restoration until the tree is fully populated
            from PySide6.QtCore import QTimer
            QTimer.singleShot(300, lambda: main_window.explorer.set_expanded_state(expanded_folders))
        
        # Restore open tabs asynchronously to avoid blocking
        open_tabs = workspace_data.get('open_tabs', [])
        current_tab_index = workspace_data.get('current_tab_index', -1)
        bdd_mode = workspace_data.get('bdd_mode', False)
        
        def restore_tabs():
            """Restore tabs one by one with delays to avoid UI freezing"""
            # Enable suppress mode to avoid triggering updates during bulk restore
            main_window._suppress_updates = True
            
            tab_index = 0
            
            def open_next_tab():
                nonlocal tab_index
                if tab_index < len(open_tabs):
                    tab_data = open_tabs[tab_index]
                    file_path = tab_data.get('file_path')
                    if file_path and os.path.exists(file_path):
                        main_window.open_file_in_tab(file_path, suppress_updates=True)
                    tab_index += 1
                    # Schedule next tab with minimal delay (10ms)
                    QTimer.singleShot(10, open_next_tab)
                else:
                    # All tabs restored, now restore current tab index
                    if current_tab_index >= 0 and current_tab_index < main_window.tabs.count():
                        main_window.tabs.setCurrentIndex(current_tab_index)
                    
                    # Apply BDD mode to all restored tabs (with deferred conversion)
                    if bdd_mode and hasattr(main_window, 'global_bdd_mode_changed'):
                        for i in range(main_window.tabs.count()):
                            widget = main_window.tabs.widget(i)
                            if hasattr(widget, 'set_global_bdd_mode'):
                                # Use defer_conversion=True for non-current tabs
                                defer = (i != current_tab_index)
                                widget.set_global_bdd_mode(bdd_mode, defer_conversion=defer)
                    
                    # Re-enable updates and trigger final update
                    main_window._suppress_updates = False
                    # Update mind map once for the current tab
                    if hasattr(main_window, '_update_mind_map_for_current_file'):
                        main_window._update_mind_map_for_current_file()
            
            # Start opening tabs
            open_next_tab()
        
        # Delay tab restoration to allow window to show first
        QTimer.singleShot(50, restore_tabs)
    
    def clear_workspace(self):
        """Clear workspace state"""
        if os.path.exists(self.workspace_file):
            try:
                os.remove(self.workspace_file)
                print(f"Cleared workspace state: {self.workspace_file}")
            except Exception as e:
                print(f"Failed to clear workspace state: {e}")
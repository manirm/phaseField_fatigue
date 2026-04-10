import wx
import wx.aui as aui
import wx.adv
from src.gui.panels import ControlPanel, PlotNotebook, ConsolePanel

class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(1200, 800))
        
        # Modern Light Theme Colors
        self.LIGHT_BG = wx.Colour(248, 249, 250)
        self.ACCENT_COLOR = wx.Colour(13, 110, 253)
        self.SetBackgroundColour(self.LIGHT_BG)
        
        # Setup AUI Manager
        self._mgr = aui.AuiManager()
        self._mgr.SetManagedWindow(self)
        
        # Create Panes
        self.console_panel = ConsolePanel(self)
        self.control_panel = ControlPanel(self)
        self.plot_notebook = PlotNotebook(self)
        
        # Add Panes to Manager
        self._mgr.AddPane(self.control_panel, aui.AuiPaneInfo().
                          Name("controls").Caption("Simulation Controls").
                          Left().Layer(1).BestSize(350, -1).
                          CloseButton(False).MaximizeButton(True))
        
        self._mgr.AddPane(self.plot_notebook, aui.AuiPaneInfo().
                          Name("plots").CenterPane())
        
        self._mgr.AddPane(self.console_panel, aui.AuiPaneInfo().
                          Name("console").Caption("Process Output").
                          Bottom().Layer(0).BestSize(-1, 150).
                          CloseButton(False).MaximizeButton(True))
        
        # Setup Menu Bar
        self.init_menubar()
        
        # Commit layout
        self._mgr.Update()
        
    def init_menubar(self):
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, "&New Simulation\tCtrl+N")
        file_menu.Append(wx.ID_OPEN, "&Open Material Library\tCtrl+O")
        file_menu.AppendSeparator()
        pref_item = file_menu.Append(wx.ID_PREFERENCES, "&Preferences/Settings\tCtrl+,")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tAlt+X")
        menubar.Append(file_menu, "&File")
        
        help_menu = wx.Menu()
        guide_item = help_menu.Append(wx.ID_HELP, "&User Guide\tF1")
        help_menu.AppendSeparator()
        about_item = help_menu.Append(wx.ID_ABOUT, "&About")
        menubar.Append(help_menu, "&Help")
        
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_preferences, pref_item)
        self.Bind(wx.EVT_MENU, self.on_open_config, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
        self.Bind(wx.EVT_MENU, self.on_user_guide, guide_item)
        
    def on_preferences(self, event):
        """Focus the Settings tab in the plot notebook."""
        # The Settings tab is index 6 (after Batch Manager)
        self.plot_notebook.SetSelection(6)
        
    def on_open_config(self, event):
        """Allow user to see/edit the material library yaml."""
        import os
        yaml_path = os.path.join(os.path.dirname(__file__), "..", "data", "materials.yaml")
        if os.path.exists(yaml_path):
            # In a real app we'd open a text editor or a dialog. 
            # For now, let's just log it to console to prove it works.
            self.console_panel.append_text(f"Opening Material Library: {yaml_path}")
            # Try to open with default system editor
            import subprocess
            try:
                subprocess.run(["open", yaml_path], check=False)
            except:
                pass

    def on_about(self, event):
        info = wx.adv.AboutDialogInfo()
        info.SetName("Phase-Field Fatigue Suite")
        info.SetVersion("1.0.0 Pro")
        info.SetDescription("A high-fidelity 3D multi-physics suite for hydrogen-assisted fatigue and fracture analysis.")
        info.SetCopyright("(C) 2026 Mohammed Maniruzzaman")
        info.SetWebSite("https://github.com/manirm/phaseField_fatigue")
        info.AddDeveloper("Design and Developed by Mohammed Maniruzzaman")
        info.AddDocWriter("Documentation by Mohammed Maniruzzaman")
        info.SetLicense("Licensed under the MIT License")
        
        wx.adv.AboutBox(info)

    def on_user_guide(self, event):
        """Open the professional multi-page documentation."""
        import os
        docs_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "site", "index.html")
        if not os.path.exists(docs_path):
            wx.MessageBox("Professional User Guide (HTML) not found in docs/site/.", 
                          "Documentation Missing", wx.ICON_INFORMATION)
        else:
            wx.LaunchDefaultBrowser(f"file://{os.path.abspath(docs_path)}")

    def on_exit(self, event):
        self.Close()
        
    def __del__(self):
        self._mgr.UnInit()

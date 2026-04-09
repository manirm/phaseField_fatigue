import wx
import wx.aui as aui
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
        self.control_panel = ControlPanel(self)
        self.plot_notebook = PlotNotebook(self)
        self.console_panel = ConsolePanel(self)
        
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
        file_menu.Append(wx.ID_OPEN, "&Open Config\tCtrl+O")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tAlt+X")
        menubar.Append(file_menu, "&File")
        
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ABOUT, "&About")
        menubar.Append(help_menu, "&Help")
        
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        
    def on_exit(self, event):
        self.Close()
        
    def __del__(self):
        self._mgr.UnInit()

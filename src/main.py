import wx
from src.gui.main_frame import MainFrame

class PhaseFieldApp(wx.App):
    def OnInit(self):
        self.SetAppName("PhaseField Fatigue")
        frame = MainFrame(None, title="Phase-Field Fatigue Analysis Suite")
        frame.Show()
        return True

if __name__ == "__main__":
    app = PhaseFieldApp()
    app.MainLoop()

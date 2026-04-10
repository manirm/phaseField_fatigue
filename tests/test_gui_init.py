import wx
import pytest
from src.main import PhaseFieldApp
from src.gui.main_frame import MainFrame

@pytest.fixture
def app():
    # Initialize wxApp
    test_app = PhaseFieldApp(False)
    yield test_app
    test_app.ExitMainLoop()

def test_app_initialization(app):
    """Verify that the PhaseFieldApp initializes correctly."""
    assert app.GetAppName() == "PhaseField Fatigue"

def test_mainframe_creation(app):
    """Verify that the MainFrame is created and has the correct title."""
    # Find the main frame among top-level windows
    tlws = wx.GetTopLevelWindows()
    main_frame = next((w for w in tlws if isinstance(w, MainFrame)), None)
    
    assert main_frame is not None
    assert "Phase-Field Fatigue" in main_frame.GetTitle()
    
    # Check for core panels
    assert hasattr(main_frame, 'control_panel')
    assert hasattr(main_frame, 'plot_notebook')
    assert hasattr(main_frame, 'console_panel')

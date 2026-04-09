import wx
import wx.lib.scrolledpanel as scrolled
import threading
import time
import os
from src.engine.mesh_gen import MeshGenerator
from src.engine.solver import PhaseFieldSolver
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.figure import Figure

class ControlPanel(scrolled.ScrolledPanel):
    def __init__(self, parent):
        super().__init__(parent)
        self.LIGHT_BG = wx.Colour(255, 255, 255)
        self.SetBackgroundColour(self.LIGHT_BG)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # --- Section: Template ---
        self.add_section_title(main_sizer, "Specimen Geometry")
        self.template_choice = wx.Choice(self, choices=["Compact Tension (CT)", "Single Edge Notch Bending (SENB)", "Custom .geo file"])
        self.template_choice.SetSelection(0)
        main_sizer.Add(self.template_choice, 0, wx.ALL | wx.EXPAND, 10)
        
        # --- Section: Material Parameters ---
        self.add_section_title(main_sizer, "Material Properties")
        self.params_grid = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        self.params_grid.AddGrowableCol(1)
        
        self.e_ctrl = self.add_input_row(self.params_grid, "Young's Modulus (E)", "210000.0", "MPa")
        self.v_ctrl = self.add_input_row(self.params_grid, "Poisson's Ratio (v)", "0.3", "-")
        self.gc_ctrl = self.add_input_row(self.params_grid, "Crit. Energy Release (Gc)", "2.7", "N/mm")
        self.l_ctrl = self.add_input_row(self.params_grid, "Length Scale (l)", "0.01", "mm")
        
        main_sizer.Add(self.params_grid, 0, wx.ALL | wx.EXPAND, 10)
        
        # --- Section: Fatigue Parameters ---
        self.add_section_title(main_sizer, "Fatigue (Paris' Law)")
        self.fatigue_grid = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        self.fatigue_grid.AddGrowableCol(1)
        
        self.c_ctrl = self.add_input_row(self.fatigue_grid, "Paris Constant (C)", "1e-12", "mm/cycle")
        self.m_ctrl = self.add_input_row(self.fatigue_grid, "Paris Exponent (m)", "3.0", "-")
        self.dp_ctrl = self.add_input_row(self.fatigue_grid, "Load Range (dP)", "100.0", "N")
        self.a0_ctrl = self.add_input_row(self.fatigue_grid, "Initial Crack (a0)", "10.0", "mm")
        
        main_sizer.Add(self.fatigue_grid, 0, wx.ALL | wx.EXPAND, 10)
        
        # --- Section: Solver & MPI ---
        self.add_section_title(main_sizer, "Solver Configuration")
        self.solver_grid = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        self.solver_grid.AddGrowableCol(1)
        
        self.lc_ctrl = self.add_input_row(self.solver_grid, "Mesh Size (lc)", "0.1", "mm")
        self.tip_refine_ctrl = self.add_input_row(self.solver_grid, "Tip Refinement", "5.0", "-")
        
        amr_label = wx.StaticText(self, label="Adaptive Meshing:")
        self.amr_toggle_ctrl = wx.CheckBox(self, label="Enable AMR (Dynamic Remesh)")
        self.solver_grid.Add(amr_label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.solver_grid.Add(self.amr_toggle_ctrl, 0, wx.EXPAND)
        
        # MPI Core selection
        cores_label = wx.StaticText(self, label="MPI Cores:")
        self.cores_spin = wx.SpinCtrl(self, value="1", min=1, max=64)
        self.solver_grid.Add(cores_label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.solver_grid.Add(self.cores_spin, 0, wx.EXPAND)
        
        main_sizer.Add(self.solver_grid, 0, wx.ALL | wx.EXPAND, 10)
        
        # Action Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.run_btn = wx.Button(self, label="Run Simulation")
        self.run_btn.SetBackgroundColour(wx.Colour(13, 110, 253))
        self.run_btn.SetForegroundColour(wx.WHITE)
        
        self.stop_btn = wx.Button(self, label="Stop")
        self.stop_btn.Disable()
        
        btn_sizer.Add(self.run_btn, 1, wx.RIGHT, 5)
        btn_sizer.Add(self.stop_btn, 0)
        
        main_sizer.AddStretchSpacer()
        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.EXPAND, 20)
        
        self.SetSizer(main_sizer)
        self.SetupScrolling()
        
        # Bind events
        self.run_btn.Bind(wx.EVT_BUTTON, self.on_run)
        self.stop_btn.Bind(wx.EVT_BUTTON, self.on_stop)

    def log(self, message):
        # Find the console panel through the parent main frame
        self.GetParent().console_panel.append_text(message)

    def on_run(self, event):
        params = {
            'template': self.template_choice.GetStringSelection(),
            'E': float(self.e_ctrl.GetValue()),
            'lc': float(self.lc_ctrl.GetValue()),
            'tip_refine': float(self.tip_refine_ctrl.GetValue()),
            'amr': self.amr_toggle_ctrl.GetValue(),
            'cores': self.cores_spin.GetValue(),
            'a0': float(self.a0_ctrl.GetValue()),
            'fatigue': {
                'C': float(self.c_ctrl.GetValue()),
                'm': float(self.m_ctrl.GetValue()),
                'dP': float(self.dp_ctrl.GetValue())
            }
        }
        self.log("Generating mesh...")
        try:
            mg = MeshGenerator()
            if "CT" in params['template']:
                params['msh_path'] = mg.generate_ct_specimen(lc=params['lc'], a=params['a0'], tip_refine=params['tip_refine'])
            else:
                params['msh_path'] = mg.generate_senb_specimen(lc=params['lc'], a=params['a0'], tip_refine=params['tip_refine'])
            self.log(f"Mesh generated at: {params['msh_path']}")
        except Exception as e:
            self.log(f"ERROR generating mesh: {str(e)}")
            return
            
        self.sim_thread = SimulationThread(self, params)
        self.sim_thread.start()

    def on_stop(self, event):
        if hasattr(self, 'sim_thread'):
            self.sim_thread.stop()
            self.log("Stopping simulation...")

    def on_sim_start(self):
        self.run_btn.Disable()
        self.stop_btn.Enable()
        self.log("--- New Simulation Started ---")

    def on_sim_progress(self, current, total, frame_data=None):
        if frame_data:
            self.GetParent().plot_notebook.update_animation(frame_data)

    def on_sim_finished(self, results=None):
        self.run_btn.Enable()
        self.stop_btn.Disable()
        if results and results.get("status") == "success":
            self.log("--- Simulation Finished ---")
            self.GetParent().plot_notebook.update_plots(results)
        else:
            self.log("--- Simulation Ended ---")
        
    def add_section_title(self, sizer, title):
        lbl = wx.StaticText(self, label=title)
        font = lbl.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        lbl.SetFont(font)
        sizer.Add(lbl, 0, wx.TOP | wx.LEFT, 15)
        line = wx.StaticLine(self)
        sizer.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

    def add_input_row(self, grid, label_text, default_val, unit):
        lbl = wx.StaticText(self, label=label_text)
        txt = wx.TextCtrl(self, value=default_val)
        unit_lbl = wx.StaticText(self, label=unit)
        
        row_sizer = wx.BoxSizer(wx.HORIZONTAL)
        row_sizer.Add(txt, 1, wx.EXPAND)
        row_sizer.Add(unit_lbl, 0, wx.LEFT, 5)
        
        grid.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(row_sizer, 0, wx.EXPAND)
        return txt

class PlotNotebook(wx.Notebook):
    def __init__(self, parent):
        super().__init__(parent)
        self.show_mesh = False
        self.phi_history = []
        self.current_frame = 0
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_playback_timer, self.timer)
        
        self.add_plot_tab("Phase-Field")
        self.add_plot_tab("Load-Displacement")
        self.add_plot_tab("Fatigue (a vs N)")
        
    def add_plot_tab(self, name):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        figure = Figure(figsize=(5, 4), dpi=100)
        figure.set_facecolor('white')
        canvas = FigureCanvas(panel, -1, figure)
        
        # Add Navigation Toolbar
        toolbar = NavigationToolbar(canvas)
        toolbar.Realize()
        
        axes = figure.add_subplot(111)
        axes.set_title(f"{name} Analysis")
        axes.grid(True, linestyle='--', alpha=0.6)
        
        sizer.Add(canvas, 1, wx.EXPAND)
        sizer.Add(toolbar, 0, wx.LEFT | wx.EXPAND)
        
        # Add Playback controls for Phase-Field
        if name == "Phase-Field":
            pb_sizer = wx.BoxSizer(wx.HORIZONTAL)
            
            self.play_btn = wx.Button(panel, label="Play")
            self.restart_btn = wx.Button(panel, label="Restart")
            self.slider = wx.Slider(panel, value=0, minValue=0, maxValue=100, style=wx.SL_HORIZONTAL)
            self.mesh_toggle = wx.CheckBox(panel, label="Show Mesh")
            
            self.play_btn.Bind(wx.EVT_BUTTON, self.on_play_toggle)
            self.restart_btn.Bind(wx.EVT_BUTTON, self.on_restart)
            self.slider.Bind(wx.EVT_SLIDER, self.on_slider_scroll)
            self.mesh_toggle.Bind(wx.EVT_CHECKBOX, self.on_mesh_toggle)
            
            pb_sizer.Add(self.play_btn, 0, wx.ALL, 5)
            pb_sizer.Add(self.restart_btn, 0, wx.ALL, 5)
            pb_sizer.Add(self.slider, 1, wx.ALL | wx.EXPAND, 5)
            pb_sizer.Add(self.mesh_toggle, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            
            sizer.Add(pb_sizer, 0, wx.EXPAND)
            
        panel.SetSizer(sizer)
        self.AddPage(panel, name)
        
        # Store for later update
        if not hasattr(self, 'plot_canvases'):
            self.plot_canvases = {}
        self.plot_canvases[name] = (canvas, figure, axes)

    def update_plots(self, results):
        self._last_results = results
        import numpy as np
        
        # 1. Update Load-Displacement
        if "load_disp" in results:
            data = results["load_disp"]
            canvas, fig, ax = self.plot_canvases["Load-Displacement"]
            ax.clear()
            ax.plot(data["u"], data["f"], 'b-', linewidth=2, label='Phase-Field Response')
            ax.set_title("Load-Displacement Curve")
            ax.set_xlabel("Displacement [mm]")
            ax.set_ylabel("Force [N]")
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.legend()
            canvas.draw()
            
        # 2. Update Mesh/Phase-Field (Final State)
        if "mesh_file" in results:
            canvas, fig, ax = self.plot_canvases["Phase-Field"]
            ax.clear()
            
            try:
                import meshio
                import numpy as np
                path = results["mesh_file"]
                if os.path.exists(path):
                    if "amr_points_history" in results and len(results["amr_points_history"]) > 0:
                        pts = results["amr_points_history"][-1]
                        cells = results["amr_cells_history"][-1]
                    else:
                        msh = meshio.read(path)
                        pts = msh.points[:, :2]
                        cells = msh.get_cells_type("triangle")
                        
                    # If we have a final phase-field (phi), show the crack
                    if "final_phi" in results:
                        phi = results["final_phi"]
                        try:
                            tc = ax.tripcolor(pts[:, 0], pts[:, 1], cells, phi, cmap='jet', vmin=0, vmax=1)
                        except Exception as tripE:
                            ax.text(0.5, 0.5, f"Plot Error:\n{str(tripE)}", ha='center', va='center', transform=ax.transAxes)
                            pass
                        if getattr(self, 'show_mesh', False):
                            ax.triplot(pts[:, 0], pts[:, 1], cells, color='white', alpha=0.5, linewidth=0.3)
                        ax.set_title("Final Crack Profile (Phase-Field \u03C6)", fontsize=10)
                        if not hasattr(self, '_colorbar'):
                             self._colorbar = fig.colorbar(tc, ax=ax, shrink=0.6, label="Damage (\u03C6)")
                    else:
                        # Fallback to mesh preview
                        if len(cells) > 50000:
                            cells_to_plot = cells[::len(cells)//10000]
                        else:
                            cells_to_plot = cells
                        ax.triplot(pts[:, 0], pts[:, 1], cells_to_plot, color='#1a73e8', alpha=0.4, linewidth=0.3)
                        ax.set_title(f"Finite Element Mesh: {os.path.basename(path)} (Preview)", fontsize=10)
                    
                    ax.set_aspect('equal')
                    ax.axis('on')
                    ax.grid(True, linestyle=':', alpha=0.3)
                else:
                    ax.text(0.5, 0.5, f"Mesh file not found at\n{path}", ha='center', va='center', transform=ax.transAxes)
            except Exception as e:
                ax.text(0.5, 0.5, f"Visualization error:\n{str(e)}", ha='center', va='center', transform=ax.transAxes)
            
            canvas.draw()
            
        # 3. Update Fatigue Life
        if "fatigue_life" in results:
            data = results["fatigue_life"]
            canvas, fig, ax = self.plot_canvases["Fatigue (a vs N)"]
            ax.clear()
            ax.plot(data["N"], data["a"], 'r-', linewidth=2, label="Paris' Law Prediction")
            ax.set_title("Crack Length vs. Cycles")
            ax.set_xlabel("Cycles (N)")
            ax.set_ylabel("Crack Length (a) [mm]")
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.legend()
            canvas.draw()
            
        # 4. Initialize Playback Buffer
        if "phi_history" in results:
            self.phi_history = results["phi_history"]
            self.anim_a_vals = results.get("a_history_anim", [])
            self.center_y = results.get("center_y", 25.0)
            self.amr_points_history = results.get("amr_points_history", [])
            self.amr_cells_history = results.get("amr_cells_history", [])
            self.slider.SetMax(len(self.phi_history) - 1)
            self.slider.SetValue(len(self.phi_history) - 1)
            self.current_frame = len(self.phi_history) - 1
            
        # Switch to results tab (Load-Displacement)
        self.SetSelection(1)

    def get_frame_data(self, idx):
        data = {
            "phi": self.phi_history[idx] if self.phi_history else None,
            "crack_a": self.anim_a_vals[idx] if getattr(self, "anim_a_vals", None) else None,
            "center_y": getattr(self, "center_y", 25.0)
        }
        if getattr(self, "amr_points_history", None) and len(self.amr_points_history) > idx:
            data["pts"] = self.amr_points_history[idx]
            data["cells"] = self.amr_cells_history[idx]
        return data

    def on_play_toggle(self, event):
        if self.timer.IsRunning():
            self.timer.Stop()
            self.play_btn.SetLabel("Play")
        else:
            if self.current_frame >= len(self.phi_history) - 1:
                self.current_frame = 0
            self.timer.Start(100) # 10 FPS
            self.play_btn.SetLabel("Pause")

    def on_restart(self, event):
        self.timer.Stop()
        self.play_btn.SetLabel("Play")
        self.current_frame = 0
        self.slider.SetValue(0)
        self.update_animation(self.get_frame_data(0))

    def on_mesh_toggle(self, event):
        self.show_mesh = self.mesh_toggle.GetValue()
        if self.phi_history:
            self.update_animation(self.get_frame_data(self.current_frame))
        elif hasattr(self, '_last_results'):
            self.update_plots(self._last_results)

    def on_slider_scroll(self, event):
        self.current_frame = self.slider.GetValue()
        if self.phi_history:
            self.update_animation(self.get_frame_data(self.current_frame))

    def on_playback_timer(self, event):
        if self.current_frame < len(self.phi_history) - 1:
            self.current_frame += 1
            self.slider.SetValue(self.current_frame)
            self.update_animation(self.get_frame_data(self.current_frame))
        else:
            self.timer.Stop()
            self.play_btn.SetLabel("Play")

    def update_animation(self, frame_data):
        import numpy as np
        if "phi" in frame_data:
            phi = frame_data["phi"]
            canvas, fig, ax = self.plot_canvases["Phase-Field"]
            
            if "pts" in frame_data and "cells" in frame_data:
                pts = frame_data["pts"]
                cells = frame_data["cells"]
            else:
                if not hasattr(self, '_anim_mesh'):
                    return
                pts, cells = self._anim_mesh
            
            ax.clear()
            tc = ax.tripcolor(pts[:, 0], pts[:, 1], cells, phi, cmap='jet', vmin=0, vmax=1)
            if getattr(self, 'show_mesh', False):
                ax.triplot(pts[:, 0], pts[:, 1], cells, color='white', alpha=0.5, linewidth=0.3)
                
            if "crack_a" in frame_data and "center_y" in frame_data:
                crack_a = frame_data["crack_a"]
                center_y = frame_data["center_y"]
                ax.plot([0, crack_a], [center_y, center_y], color='red', linewidth=2.5, linestyle='-')
                
            ax.set_title("Crack Propagation (Phase-Field \u03C6)", fontsize=10)
            ax.set_aspect('equal')
            ax.axis('off')
            
            if not hasattr(self, '_colorbar'):
                 self._colorbar = fig.colorbar(tc, ax=ax, shrink=0.6, label="Damage (\u03C6)")
            
            canvas.draw()

class ConsolePanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetBackgroundColour(wx.Colour(240, 240, 240))
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.log_text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH)
        self.log_text.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.log_text.SetForegroundColour(wx.Colour(33, 37, 41))
        self.log_text.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        sizer.Add(self.log_text, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def append_text(self, text):
        self.log_text.AppendText(text + "\n")

class SimulationThread(threading.Thread):
    def __init__(self, panel, params):
        super().__init__()
        self.panel = panel
        self.params = params
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        wx.CallAfter(self.panel.on_sim_start)
        
        try:
            msh_path = self.params['msh_path']
            solver = PhaseFieldSolver(msh_path, self.params, mpi_cores=self.params['cores'])
            
            def progress(current, total, frame_data=None):
                if self._stop_event.is_set():
                    raise InterruptedError("Simulation stopped by user")
                wx.CallAfter(self.panel.on_sim_progress, current, total, frame_data)
            
            # Pre-load mesh for animation in GUI thread
            import meshio
            msh = meshio.read(msh_path)
            self.panel.GetParent().plot_notebook._anim_mesh = (msh.points[:, :2], msh.get_cells_type("triangle"))
            
            results = solver.run(progress_callback=progress)
            wx.CallAfter(self.panel.log, f"Simulation completed. Status: {results['status']}")
            wx.CallAfter(self.panel.on_sim_finished, results)
            
        except Exception as e:
            wx.CallAfter(self.panel.log, f"ERROR: {str(e)}")
            wx.CallAfter(self.panel.on_sim_finished, None)

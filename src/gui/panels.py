import wx
import wx.svg
import wx.lib.scrolledpanel as scrolled
import threading
import time
import os
import yaml
import numpy as np
from src.engine.mesh_gen import MeshGenerator
from src.engine.solver import PhaseFieldSolver
from src.engine.batch_manager import BatchManager
from src.config import config
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.tri as mtri

class ControlPanel(scrolled.ScrolledPanel):
    def __init__(self, parent):
        super().__init__(parent)
        self.LIGHT_BG = wx.Colour(255, 255, 255)
        self.SetBackgroundColour(self.LIGHT_BG)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # --- Section: Template ---
        self.add_section_title(main_sizer, "Specimen Geometry")
        self.template_choice = wx.Choice(self, choices=["Compact Tension (CT)", "Single Edge Notch Bending (SENB)", "Center-Cracked Tension (CCT)", "Custom .geo file"])
        self.template_choice.SetSelection(0)
        self.preview_btn = wx.Button(self, label="Preview Mesh")
        
        # Specimen Thumbnail
        self.icon_panel = wx.Panel(self, size=(100, 100))
        self.icon_panel.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.icon_panel.Bind(wx.EVT_PAINT, self.on_paint_icon)
        
        geom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        choice_sizer = wx.BoxSizer(wx.VERTICAL)
        choice_sizer.Add(self.template_choice, 0, wx.EXPAND | wx.BOTTOM, 5)
        choice_sizer.Add(self.preview_btn, 0, wx.EXPAND)
        
        geom_sizer.Add(self.icon_panel, 0, wx.RIGHT, 15)
        geom_sizer.Add(choice_sizer, 1, wx.ALIGN_CENTER_VERTICAL)
        
        main_sizer.Add(geom_sizer, 0, wx.ALL | wx.EXPAND, 15)
        
        # --- Section: Material Parameters ---
        self.add_section_title(main_sizer, "Material Properties")
        self.params_grid = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        self.params_grid.AddGrowableCol(1)
        
        # Material Preset
        self.load_materials()
        mat_label = wx.StaticText(self, label="Material Preset:")
        self.mat_choice = wx.Choice(self, choices=["-- Select Preset --"] + self.material_names)
        self.mat_choice.SetSelection(0)
        self.params_grid.Add(mat_label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.params_grid.Add(self.mat_choice, 0, wx.EXPAND)
        
        self.e_ctrl = self.add_input_row(self.params_grid, "Young's Modulus (E)", "210000.0", "MPa")
        self.v_ctrl = self.add_input_row(self.params_grid, "Poisson's Ratio (v)", "0.3", "-")
        self.gc_ctrl = self.add_input_row(self.params_grid, "Crit. Energy Release (Gc)", "2.7", "N/mm")
        self.l_ctrl = self.add_input_row(self.params_grid, "Length Scale (l)", "0.01", "mm")
        
        main_sizer.Add(self.params_grid, 0, wx.ALL | wx.EXPAND, 10)
        
        self.fatigue_grid = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        self.fatigue_grid.AddGrowableCol(1)
        
        # We wrap the fatigue inputs in a sizer so we can hide/show them
        self.fatigue_inputs_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.c_ctrl = self.add_input_row(self.fatigue_grid, "Paris Constant (C)", "1e-12", "mm/cycle")
        self.m_ctrl = self.add_input_row(self.fatigue_grid, "Paris Exponent (m)", "3.0", "-")
        self.dp_ctrl = self.add_input_row(self.fatigue_grid, "Load Range (dP)", "100.0", "N")
        self.a0_ctrl = self.add_input_row(self.fatigue_grid, "Initial Crack (a0)", "10.0", "mm")
        
        self.fatigue_title = self.add_section_title(main_sizer, "Fatigue (Paris' Law)")
        main_sizer.Add(self.fatigue_grid, 0, wx.ALL | wx.EXPAND, 10)
        
        # --- Section: Solver & MPI ---
        self.add_section_title(main_sizer, "Solver Configuration")
        self.solver_grid = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        self.solver_grid.AddGrowableCol(1)
        
        self.lc_ctrl = self.add_input_row(self.solver_grid, "Mesh Size (lc)", "0.1", "mm")
        self.tip_refine_ctrl = self.add_input_row(self.solver_grid, "Tip Refinement", "5.0", "-")
        self.thickness_ctrl = self.add_input_row(self.solver_grid, "Thickness (B)", "10.0", "mm")
        
        # We'll hide/show the fatigue_grid and fatigue_title instead of parents
        
        amr_label = wx.StaticText(self, label="Adaptive Meshing:")
        self.amr_toggle_ctrl = wx.CheckBox(self, label="Enable AMR (Dynamic Remesh)")
        self.solver_grid.Add(amr_label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.solver_grid.Add(self.amr_toggle_ctrl, 0, wx.EXPAND)
        
        # MPI Core selection
        cores_label = wx.StaticText(self, label="MPI Cores:")
        self.cores_spin = wx.SpinCtrl(self, value="1", min=1, max=64)
        self.solver_grid.Add(cores_label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.solver_grid.Add(self.cores_spin, 0, wx.EXPAND)
        
        sym_label = wx.StaticText(self, label="Symmetry:")
        self.sym_toggle_ctrl = wx.CheckBox(self, label="Enable Symmetry (Half/Quarter)")
        self.solver_grid.Add(sym_label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.solver_grid.Add(self.sym_toggle_ctrl, 0, wx.EXPAND)
        
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
        self.preview_btn.Bind(wx.EVT_BUTTON, self.on_preview_mesh)
        self.mat_choice.Bind(wx.EVT_CHOICE, self.on_material_preset)
        self.template_choice.Bind(wx.EVT_CHOICE, self.on_template_change)

    def on_template_change(self, event):
        self.icon_panel.Refresh()

    def on_paint_icon(self, event):
        dc = wx.PaintDC(self.icon_panel)
        gc = wx.GraphicsContext.Create(dc)
        if not gc: return
        
        template = self.template_choice.GetStringSelection()
        icon_name = "ct_icon.svg"
        if "SENB" in template: icon_name = "senb_icon.svg"
        elif "CCT" in template: icon_name = "cct_icon.svg"
        
        icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "icons", icon_name)
        if os.path.exists(icon_path):
            try:
                img = wx.svg.SVGimage.CreateFromFile(icon_path)
                bmp = img.ConvertToBitmap(width=80, height=80)
                gc.DrawBitmap(bmp, 10, 10, 80, 80)
            except Exception as e:
                print(f"Error drawing SVG: {e}")

    def load_materials(self):
        self.materials = {}
        self.material_names = []
        try:
            yaml_path = os.path.join(os.path.dirname(__file__), "..", "data", "materials.yaml")
            if os.path.exists(yaml_path):
                with open(yaml_path, 'r') as f:
                    self.materials = yaml.safe_load(f)
                    self.material_names = [m['name'] for m in self.materials.values()]
        except Exception as e:
            print(f"Error loading materials: {e}")
        # Force a GUI update to ensure the message is seen immediately
        wx.SafeYield()

    def get_params(self):
        """Extract all current UI parameters into a dictionary."""
        return {
            'template': self.template_choice.GetStringSelection(),
            'E': float(self.e_ctrl.GetValue()),
            'nu': float(self.v_ctrl.GetValue()),
            'Gc': float(self.gc_ctrl.GetValue()),
            'lc': float(self.lc_ctrl.GetValue()),
            'tip_refine': float(self.tip_refine_ctrl.GetValue()),
            'amr': self.amr_toggle_ctrl.GetValue(),
            'symmetry': self.sym_toggle_ctrl.GetValue(),
            'cores': self.cores_spin.GetValue(),
            'a0': float(self.a0_ctrl.GetValue()),
            'mode': config.mode,
            'dimension': config.dimension,
            'thickness': float(self.thickness_ctrl.GetValue()),
            'energy_split': config.energy_split,
            'solver_tol': config.solver_tol,
            'hydrogen_enabled': config.hydrogen_enabled,
            'chi': config.chi,
            'c0': config.c0,
            'exposure_mode': config.exposure_mode,
            'material': {
                'E': float(self.e_ctrl.GetValue()),
                'nu': float(self.v_ctrl.GetValue()),
                'Gc': float(self.gc_ctrl.GetValue()),
                'C': float(self.c_ctrl.GetValue()),
                'm': float(self.m_ctrl.GetValue()),
                'chi': config.chi,
                'D': config.diff_coeff
            }
        }

    def on_run(self, event):
        params = self.get_params()
        self.log("Generating mesh...")
        try:
            mg = MeshGenerator()
            if "CT" in params['template']:
                params['msh_path'] = mg.generate_ct_specimen(lc=params['lc'], a=params['a0'], tip_refine=params['tip_refine'],
                                                              is_3d=(params['dimension'] == '3D'), thickness=params['thickness'])
            elif "SENB" in params['template']:
                params['msh_path'] = mg.generate_senb_specimen(lc=params['lc'], a=params['a0'], tip_refine=params['tip_refine'], 
                                                               symmetry=params['symmetry'], is_3d=(params['dimension'] == '3D'), thickness=params['thickness'])
            elif "CCT" in params['template']:
                params['msh_path'] = mg.generate_cct_specimen(lc=params['lc'], a=params['a0'], tip_refine=params['tip_refine'], 
                                                               symmetry=params['symmetry'], is_3d=(params['dimension'] == '3D'), thickness=params['thickness'])
            else:
                self.log("ERROR: Custom .geo selection not yet implemented.")
                return
            self.log(f"Mesh generated at: {params['msh_path']}")
        except Exception as e:
            self.log(f"ERROR generating mesh: {str(e)}")
            return
            
        self.sim_thread = SimulationThread(self, params)
        self.sim_thread.start()

    def on_preview_mesh(self, event):
        self.log("Generating preview mesh...")
        params = {
            'template': self.template_choice.GetStringSelection(),
            'lc': float(self.lc_ctrl.GetValue()),
            'tip_refine': float(self.tip_refine_ctrl.GetValue()),
            'symmetry': self.sym_toggle_ctrl.GetValue(),
            'a0': float(self.a0_ctrl.GetValue()),
            'is_3d': (config.dimension == "3D"),
            'thickness': float(self.thickness_ctrl.GetValue())
        }
        try:
            mg = MeshGenerator()
            if "CT" in params['template']:
                path = mg.generate_ct_specimen(lc=params['lc'], a=params['a0'], tip_refine=params['tip_refine'], 
                                               is_3d=params['is_3d'], thickness=params['thickness'])
            elif "SENB" in params['template']:
                path = mg.generate_senb_specimen(lc=params['lc'], a=params['a0'], tip_refine=params['tip_refine'], 
                                                 symmetry=params['symmetry'], is_3d=params['is_3d'], thickness=params['thickness'])
            elif "CCT" in params['template']:
                path = mg.generate_cct_specimen(lc=params['lc'], a=params['a0'], tip_refine=params['tip_refine'], 
                                                 symmetry=params['symmetry'], is_3d=params['is_3d'], thickness=params['thickness'])
            else:
                self.log("ERROR: Custom .geo selection not yet implemented.")
                return
            
            self.log(f"Preview mesh ready: {path}")
            # Show in Phase-Field tab
            self.GetParent().plot_notebook.update_plots({"mesh_file": path, "status": "preview"})
        except Exception as e:
            self.log(f"ERROR: {e}")

    def on_material_preset(self, event):
        idx = self.mat_choice.GetSelection()
        if idx == 0: return # "-- Select Preset --"
        
        mat_name = self.mat_choice.GetStringSelection()
        # Find the key in materials dict
        for key, data in self.materials.items():
            if data['name'] == mat_name:
                self.e_ctrl.SetValue(str(data['E']))
                self.v_ctrl.SetValue(str(data['nu']))
                self.gc_ctrl.SetValue(str(data['Gc']))
                self.c_ctrl.SetValue(str(data['C']))
                self.m_ctrl.SetValue(str(data['m']))
                self.log(f"Loaded preset: {mat_name}")
                break

    def refresh_mode(self):
        """Update UI based on global config mode and dimension."""
        is_quick = (config.mode == "Quick")
        is_3d = (config.dimension == "3D")
        
        # Show/Hide Fatigue parameters for Quick Mode
        self.fatigue_grid.ShowItems(is_quick)
        self.fatigue_title.Show(is_quick)
        
        # Show/Hide Thickness for 3D
        # For thickness_ctrl, it resides in solver_grid. 
        # We need to find its children in solver_grid and hide those.
        # But for now, just toggling the control itself is safer than hiding parent.
        self.thickness_ctrl.Show(is_3d)
        
        self.Layout()
        self.Refresh()
        self.SendSizeEvent() # Force layout recalculation

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
            # Handle textual logs from solver
            if "log" in frame_data:
                self.log(frame_data["log"])
            
            # Handle graphical updates
            if "phi" in frame_data:
                self.GetParent().plot_notebook.update_animation(frame_data)
                # Log progress percentage periodically
                percentage = (current + 1) / total * 100
                crack_a = frame_data.get('crack_a', 0)
                if (current + 1) % 5 == 0 or (current + 1) == total:
                    self.log(f"Solving Phase-Field: {percentage:3.0f}% complete | Current crack a = {crack_a:.2f} mm")
        
        # Note: If no frame_data, it's just a generic progress pulse

    def on_sim_finished(self, results=None):
        self.run_btn.Enable()
        self.stop_btn.Disable()
        if results and results.get("status") == "success":
            self.log("--- Simulation Finished ---")
            self.GetParent().plot_notebook.update_plots(results)
        else:
            self.log("--- Simulation Ended ---")
        
    def add_section_title(self, sizer, title):
        container = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(self, label=title)
        font = lbl.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        lbl.SetFont(font)
        container.Add(lbl, 0, wx.TOP | wx.LEFT, 15)
        line = wx.StaticLine(self)
        container.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        sizer.Add(container, 0, wx.EXPAND)
        return container

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
        self.add_plot_tab("S.I.F. (K)")
        self.add_plot_tab("Hydrogen Mapping")
        
        # 6. Batch Manager Tab
        self.batch_panel = BatchManagerTab(self)
        self.AddPage(self.batch_panel, "Batch Manager")
        
        # 7. Settings Tab
        self.settings_panel = SettingsPanel(self)
        self.AddPage(self.settings_panel, "Settings")
        
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
            self.plot_type_radio = wx.RadioBox(panel, choices=["Damage (\u03C6)", "Strain Energy (W)"], 
                                             style=wx.RA_SPECIFY_COLS, majorDimension=2)
            self.export_btn = wx.Button(panel, label="Export (XDMF)")
            
            self.play_btn.Bind(wx.EVT_BUTTON, self.on_play_toggle)
            self.restart_btn.Bind(wx.EVT_BUTTON, self.on_restart)
            self.slider.Bind(wx.EVT_SLIDER, self.on_slider_scroll)
            self.mesh_toggle.Bind(wx.EVT_CHECKBOX, self.on_mesh_toggle)
            self.export_btn.Bind(wx.EVT_BUTTON, self.on_export)
            
            pb_sizer.Add(self.play_btn, 0, wx.ALL, 5)
            pb_sizer.Add(self.restart_btn, 0, wx.ALL, 5)
            pb_sizer.Add(self.slider, 1, wx.ALL | wx.EXPAND, 5)
            pb_sizer.Add(self.plot_type_radio, 0, wx.ALL, 5)
            pb_sizer.Add(self.mesh_toggle, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            pb_sizer.Add(self.export_btn, 0, wx.ALL, 5)
            
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
            canvas.Update()
            
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
            canvas.Update()
            
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
            canvas.Update()
            
        # 4. Update SIF (K)
        if "sif_k_history" in results:
            canvas, fig, ax = self.plot_canvases.get("S.I.F. (K)", (None, None, None))
            if canvas:
                ax.clear()
                a_vals = results.get('a_history_anim', [])
                k_vals = results['sif_k_history']
                if k_vals:
                    # Plot only up to the length of k_vals in case of mismatch
                    ax.plot(a_vals[:len(k_vals)], k_vals, 'r-', linewidth=2, label="S.I.F. (K_I)")
                    ax.set_title("Stress Intensity Factor (K) vs Crack Length", fontsize=10)
                    ax.set_ylabel("K_I (MPa\u221Amm)")
                    ax.set_xlabel("Crack Length a (mm)")
                    ax.grid(True, linestyle='--', alpha=0.6)
                    ax.legend()
                    canvas.draw()
                    canvas.Update()
            
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

    def on_export(self, event):
        if not self.phi_history:
            wx.MessageBox("No simulation data to export.", "Error", wx.OK | wx.ICON_ERROR)
            return
            
        with wx.FileDialog(self, "Export XDMF", wildcard="XDMF files (*.xdmf)|*.xdmf",
                         style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            path = fileDialog.GetPath()
            
            try:
                from src.engine.export import XDMFExport
                # Use the mesh file path from the results
                msh_path = getattr(self, "msh_file", "meshes/ct_specimen.msh")
                XDMFExport.save_time_series(msh_path, self.phi_history, path)
                wx.MessageBox(f"Successfully exported to {path}", "Success", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"Export failed: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

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
            
            # Select map based on UI radio choice
            if self.plot_type_radio.GetSelection() == 0:
                cmap = 'jet'
                map_data = phi
                label = "Damage (\u03C6)"
            else:
                cmap = 'viridis'
                # Simulate energy density if not explicitly passed
                map_data = (phi**2 + 1e-4) * 1000 
                label = "Energy Density (W)"
                
            tc = ax.tripcolor(pts[:, 0], pts[:, 1], cells, map_data, cmap=cmap)
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
            
        # 2. Update Hydrogen Mapping Tab
        if "ch" in frame_data and frame_data["ch"] is not None:
            canvas, fig, ax = self.plot_canvases["Hydrogen Mapping"]
            ch = frame_data["ch"]
            
            # Recalculate or use existing mesh
            if "pts" in frame_data and "cells" in frame_data:
                pts = frame_data["pts"]
                cells = frame_data["cells"]
            else:
                if not hasattr(self, '_anim_mesh'): return
                pts, cells = self._anim_mesh
            
            ax.clear()
            # Use 'plasma' or 'inferno' for high-contrast multi-physics
            tc = ax.tripcolor(pts[:, 0], pts[:, 1], cells, ch, cmap='plasma')
            ax.set_title("Hydrogen Lattice Occupancy (\u03B8)", fontsize=10)
            ax.set_aspect('equal')
            ax.axis('off')
            
            if not hasattr(self, '_ch_colorbar'):
                 self._ch_colorbar = fig.colorbar(tc, ax=ax, shrink=0.6, label="Occupancy")
            
            canvas.draw()

class SettingsPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.notebook = parent
        self.SetBackgroundColour(wx.WHITE)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        title_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title = wx.StaticText(self, label="Advanced Simulation Settings")
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL, 15)
        
        # Mode Selection
        mode_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "Core Selection")
        
        self.mode_radio = wx.RadioBox(self, label="Simulation Mode", 
                                    choices=["Quick (Analytical Paris Law)", "Full (Variational Phase-Field)"],
                                    majorDimension=1, style=wx.RA_SPECIFY_COLS)
        self.mode_radio.SetSelection(0 if config.mode == "Quick" else 1)
        mode_sizer.Add(self.mode_radio, 0, wx.ALL | wx.EXPAND, 10)
        
        self.dim_radio = wx.RadioBox(self, label="Dimension", 
                                   choices=["2D (Plane Strain)", "3D (Extruded Volume)"],
                                   majorDimension=2, style=wx.RA_SPECIFY_COLS)
        self.dim_radio.SetSelection(0 if config.dimension == "2D" else 1)
        mode_sizer.Add(self.dim_radio, 0, wx.ALL | wx.EXPAND, 10)
        
        main_sizer.Add(mode_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        # Physics Parameters
        phys_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "Variational Physics (Full Mode Only)")
        
        grid = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        grid.AddGrowableCol(1)
        
        split_label = wx.StaticText(self, label="Energy Splitting:")
        self.split_choice = wx.Choice(self, choices=["Isotropic", "Amor (Volumetric)", "Miehe (Spectral Anisotropic)"])
        self.split_choice.SetSelection(["Isotropic", "Amor", "Miehe"].index(config.energy_split))
        grid.Add(split_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.split_choice, 0, wx.EXPAND)
        
        tol_label = wx.StaticText(self, label="Solver Tolerance:")
        self.tol_ctrl = wx.TextCtrl(self, value=str(config.solver_tol))
        grid.Add(tol_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.tol_ctrl, 0, wx.EXPAND)
        
        phys_sizer.Add(grid, 0, wx.ALL | wx.EXPAND, 10)
        main_sizer.Add(phys_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        # Environmental Fatigue Section
        env_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "Environmental Fatigue (Hydrogen)")
        env_grid = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        env_grid.AddGrowableCol(1)
        
        self.h_enabled_chk = wx.CheckBox(self, label="Enable Hydrogen Multi-Physics")
        self.h_enabled_chk.SetValue(config.hydrogen_enabled)
        env_grid.Add(wx.StaticText(self, label="Activation:"), 0, wx.ALIGN_CENTER_VERTICAL)
        env_grid.Add(self.h_enabled_chk, 0, wx.EXPAND)
        
        self.h_c0_ctrl = wx.TextCtrl(self, value=str(config.c0))
        env_grid.Add(wx.StaticText(self, label="Source Conc. (C0):"), 0, wx.ALIGN_CENTER_VERTICAL)
        env_grid.Add(self.h_c0_ctrl, 0, wx.EXPAND)
        
        self.h_chi_ctrl = wx.TextCtrl(self, value=str(config.chi))
        env_grid.Add(wx.StaticText(self, label="H-Sensitivity (\u03C7):"), 0, wx.ALIGN_CENTER_VERTICAL)
        env_grid.Add(self.h_chi_ctrl, 0, wx.EXPAND)
        
        self.h_exposure_choice = wx.Choice(self, choices=["Static Boundary", "Dynamic Surface"])
        self.h_exposure_choice.SetStringSelection(config.exposure_mode)
        env_grid.Add(wx.StaticText(self, label="Exposure Mode:"), 0, wx.ALIGN_CENTER_VERTICAL)
        env_grid.Add(self.h_exposure_choice, 0, wx.EXPAND)
        
        env_sizer.Add(env_grid, 0, wx.ALL | wx.EXPAND, 10)
        main_sizer.Add(env_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        # Apply Button
        self.apply_btn = wx.Button(self, label="Apply Global Settings")
        self.apply_btn.SetBackgroundColour(wx.Colour(25, 135, 84))
        self.apply_btn.SetForegroundColour(wx.WHITE)
        main_sizer.Add(self.apply_btn, 0, wx.ALL | wx.ALIGN_RIGHT, 15)
        
        self.SetSizer(main_sizer)
        
        # Bindings
        self.apply_btn.Bind(wx.EVT_BUTTON, self.on_apply)

    def on_apply(self, event):
        config.mode = "Quick" if self.mode_radio.GetSelection() == 0 else "Full"
        config.dimension = "2D" if self.dim_radio.GetSelection() == 0 else "3D"
        config.energy_split = ["Isotropic", "Amor", "Miehe"][self.split_choice.GetSelection()]
        config.solver_tol = float(self.tol_ctrl.GetValue())
        
        # New Hydrogen Config
        config.hydrogen_enabled = self.h_enabled_chk.GetValue()
        config.c0 = float(self.h_c0_ctrl.GetValue())
        config.chi = float(self.h_chi_ctrl.GetValue())
        config.exposure_mode = self.h_exposure_choice.GetStringSelection()
        
        # Notify ControlPanel to refresh its layout
        main_frame = self.GetParent().GetParent() 
        main_frame.control_panel.refresh_mode()
        
        wx.MessageBox("Settings applied successfully! Some changes may require a new simulation to take effect.", 
                      "Settings Updated", wx.OK | wx.ICON_INFORMATION)

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
        self.log_text.SetInsertionPointEnd()
        self.log_text.Update()

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
            
            from src.engine.post_processing import CrackTracker
            
            def progress(current, total, frame_data=None):
                if self._stop_event.is_set():
                    raise InterruptedError("Simulation stopped by user")
                
                # Update crack tracking data if available
                if frame_data and "phi" in frame_data:
                    a = CrackTracker.calculate_crack_length(
                        msh.points[:, :2], 
                        frame_data["phi"], 
                        self.params.get('a0', 10.0),
                        template=self.params.get('template', 'CT')
                    )
                    frame_data["crack_a_measured"] = a
                
                # Tracking for SIF plot
                if not hasattr(self, 'sif_k_history'):
                    self.sif_k_history = []
                if frame_data and "sif_k" in frame_data:
                    self.sif_k_history.append(frame_data['sif_k'])
                
                summary = {
                    "phi": frame_data['phi'] if frame_data else None,
                    "crack_a": frame_data['crack_a'] if frame_data else 0,
                    "sif_k_history": self.sif_k_history,
                    "a_history_anim": results.get('a_history_anim', []) if 'results' in locals() else []
                }
                if frame_data and "pts" in frame_data:
                    summary["pts"] = frame_data["pts"]
                    summary["cells"] = frame_data["cells"]
                    
                wx.CallAfter(self.panel.on_sim_progress, current, total, summary)
            
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
class BatchManagerTab(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetBackgroundColour(wx.WHITE)
        self.manager = BatchManager(self)
        
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Left Panel: DOE Builder
        left_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "Parametric Sweep (Grid Search)")
        
        grid = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)
        grid.Add(wx.StaticText(self, label="Parameter"))
        grid.Add(wx.StaticText(self, label="Values (Comma Sep.)"))
        grid.Add(wx.StaticText(self, label="Enable"))
        
        self.params_ui = {}
        for p in ["Gc", "chi", "lc", "E"]:
            lbl = wx.StaticText(self, label=p)
            txt = wx.TextCtrl(self, value="1.0, 2.0" if p == "Gc" else "0.5")
            chk = wx.CheckBox(self)
            if p == "Gc": chk.SetValue(True)
            
            grid.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL)
            grid.Add(txt, 1, wx.EXPAND)
            grid.Add(chk, 0, wx.ALIGN_CENTER)
            self.params_ui[p] = (txt, chk)
            
        left_sizer.Add(grid, 0, wx.ALL | wx.EXPAND, 10)
        
        self.run_btn = wx.Button(self, label="Generate & Run Batch")
        self.run_btn.SetBackgroundColour(wx.Colour(13, 110, 253))
        self.run_btn.SetForegroundColour(wx.WHITE)
        left_sizer.Add(self.run_btn, 0, wx.ALL | wx.EXPAND, 10)
        
        self.status_lbl = wx.StaticText(self, label="Queue: Idle")
        left_sizer.Add(self.status_lbl, 0, wx.ALL, 10)
        
        main_sizer.Add(left_sizer, 1, wx.EXPAND | wx.ALL, 10)
        
        # Right Panel: Sensitivity Plot
        right_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "Sensitivity Analysis")
        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvas(self, -1, self.fig)
        right_sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 5)
        
        main_sizer.Add(right_sizer, 1, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(main_sizer)
        
        self.run_btn.Bind(wx.EVT_BUTTON, self.on_run)

    def on_run(self, event):
        sweep = {}
        for p, (txt, chk) in self.params_ui.items():
            if chk.GetValue():
                try:
                    vals = [float(x.strip()) for x in txt.GetValue().split(",")]
                    sweep[p] = vals
                except:
                    wx.MessageBox(f"Invalid values for {p}", "Input Error", wx.ICON_ERROR)
                    return
        
        # Use current main panel params as base
        main_frame = self.GetParent().GetParent()
        base_params = main_frame.control_panel.get_params()
        
        n = self.manager.generate_grid_search(base_params, sweep)
        self.status_lbl.SetLabel(f"Queue: {n} Jobs Generated. Running...")
        self.manager.run_batch(max_workers=2)

    def on_batch_job_start(self, job_id):
        print(f"Batch Job {job_id} started...")

    def on_batch_job_complete(self, job_id, summary):
        print(f"Batch Job {job_id} complete: {summary.get('status', 'Unknown')}")

    def on_batch_finished(self, results):
        self.status_lbl.SetLabel("Queue: Finished")
        # Plot Sensitivity: Max Load vs First Swept Parameter
        if not results: return
        
        job0_params = results[0]["params"]
        # Find which parameter was swept (has different values in results)
        swept_param = None
        for p in ["Gc", "chi", "lc", "E"]:
            vals = set(r["params"].get(p) for r in results if r["status"] == "Success")
            if len(vals) > 1:
                swept_param = p
                break
        
        if not swept_param: swept_param = "job_id"
        
        x = [r["params"].get(swept_param, i) if swept_param != "job_id" else i for i, r in enumerate(results)]
        y = [r["max_load"] for r in results]
        
        self.ax.clear()
        self.ax.plot(x, y, 'o-', color='#dc3545', linewidth=2, markersize=8)
        self.ax.set_xlabel(swept_param, fontweight='bold', color='#495057')
        self.ax.set_ylabel("Peak Load (N)", fontweight='bold', color='#495057')
        self.ax.set_title(f"Sensitivity Analysis: {swept_param} Variation", fontsize=11, fontweight='bold')
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.canvas.draw()

import os
import itertools
import threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import wx
from src.engine.solver import PhaseFieldSolver

class BatchManager:
    """
    Manages a queue of simulation jobs for parametric studies.
    """
    def __init__(self, panel):
        self.panel = panel
        self.queue = []
        self.results_summary = []
        self.is_running = False
        self._stop_event = threading.Event()

    def generate_grid_search(self, base_params, sweep_params):
        """
        sweep_params: dict where values are lists of values to sweep.
        Example: {'Gc': [2.0, 3.0, 4.0], 'chi': [0.5, 0.9]}
        """
        keys = sweep_params.keys()
        values = sweep_params.values()
        combinations = list(itertools.product(*values))
        
        jobs = []
        for combo in combinations:
            job_params = base_params.copy()
            for key, val in zip(keys, combo):
                if key in ['E', 'nu', 'Gc', 'C', 'm', 'chi', 'D']:
                    # Update material sub-dict if exists, or top level
                    if 'material' not in job_params: job_params['material'] = {}
                    job_params['material'][key] = val
                    job_params[key] = val
                else:
                    job_params[key] = val
            jobs.append(job_params)
        
        self.queue = jobs
        return len(jobs)

    def run_batch(self, max_workers=2):
        self.is_running = True
        self._stop_event.clear()
        self.results_summary = []
        
        def job_wrapper(params, job_id):
            if self._stop_event.is_set(): return None
            
            try:
                # Update UI for start
                wx.CallAfter(self.panel.on_batch_job_start, job_id)
                
                solver = PhaseFieldSolver(params['msh_path'], params)
                results = solver.run()
                
                # Extract key metrics for sensitivity
                summary = {
                    "job_id": job_id,
                    "params": params,
                    "max_load": np.max(results["load_disp"]["f"]) if results else 0,
                    "status": "Success" if results else "Failed"
                }
                
                wx.CallAfter(self.panel.on_batch_job_complete, job_id, summary)
                return summary
            except Exception as e:
                wx.CallAfter(self.panel.on_batch_job_complete, job_id, {"status": f"Error: {str(e)}"})
                return None

        thread = threading.Thread(target=self._executor_thread, args=(max_workers, job_wrapper))
        thread.start()

    def _executor_thread(self, max_workers, job_wrapper):
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(job_wrapper, p, i) for i, p in enumerate(self.queue)]
            for future in futures:
                res = future.result()
                if res: self.results_summary.append(res)
        
        self.is_running = False
        wx.CallAfter(self.panel.on_batch_finished, self.results_summary)

    def stop(self):
        self._stop_event.set()
        self.is_running = False

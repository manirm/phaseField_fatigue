import meshio
import os
import numpy as np

class XDMFExport:
    """
    Utility to export simulation results to XDMF/ParaView formats.
    """
    @staticmethod
    def save_final_state(msh_path, phi, output_path):
        """
        Save the final state of the simulation as a single XDMF file.
        """
        msh = meshio.read(msh_path)
        # Add phi to point data
        msh.point_data = {"phi": phi}
        msh.write(output_path)
        return output_path

    @staticmethod
    def save_time_series(msh_path, phi_history, output_path):
        """
        Save the full history of the simulation as a time-series XDMF.
        Note: Requires meshio >= 5.0
        """
        msh = meshio.read(msh_path)
        points = msh.points
        cells = msh.cells_dict
        
        # Simplified time-series export using meshio.xdmf.TimeSeriesWriter
        # If TimeSeriesWriter is not available in the current environment, 
        # we fall back to saving individual frames.
        try:
            with meshio.xdmf.TimeSeriesWriter(output_path) as writer:
                writer.write_points_cells(points, cells)
                for i, phi in enumerate(phi_history):
                    writer.write_data(float(i), point_data={"phi": phi})
            return output_path
        except Exception as e:
            # Fallback: Save as a collection of .vtu files? 
            # For now, we'll just log the error and return None if it fails.
            print(f"XDMF TimeSeries Export Error: {str(e)}")
            return None

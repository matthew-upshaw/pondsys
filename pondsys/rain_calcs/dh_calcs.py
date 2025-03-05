import os
import pandas as pd
from scipy.interpolate import LinearNDInterpolator

directory_path = os.path.dirname(__file__)

open_scupper = pd.read_csv(
    os.path.join(directory_path, 'data/open_scupper.csv'),
)
closed_scupper = pd.read_csv(
    os.path.join(directory_path, 'data/closed_scupper.csv'),
)
circular_scupper = pd.read_csv(
    os.path.join(directory_path, 'data/circular_scupper.csv'),
)

os_interp = LinearNDInterpolator(
    list(
        zip(
            open_scupper.Q,
            open_scupper.W,
        )
    ),
    open_scupper.dh
)

cls_interp = LinearNDInterpolator(
    list(
        zip(
            closed_scupper.Q,
            closed_scupper.W,
            closed_scupper.H,
        )
    ),
    closed_scupper.dh
)

crcs_interp = LinearNDInterpolator(
    list(
        zip(
            circular_scupper.Q,
            circular_scupper.D,
        )
    ),
    circular_scupper.dh
)

def open_scupper_dh(flow_rate, width):
    """
    Calculates the interpolated hydraulic head (in inches) for the given flow
    rate and scupper opening width, based on ASCE Table C8.3-3.

    Parameters
    ----------
    flow_rate : float or int
        The flow rate to the scupper in gal/min
    width : float or int
        The width of the scupper opening in inches.
    """
    return os_interp(float(flow_rate), float(width))

def closed_scupper_dh(flow_rate, width, height):
    """
    Calculates the interpolated hydraulic head (in inches) for the given flow
    rate and scupper opening width, based on ASCE Table C8.3-3.

    Parameters
    ----------
    flow_rate : float or int
        The flow rate to the scupper in gal/min
    width : float or int
        The width of the scupper opening in inches.
    height : float or int
        The height of the scupper opening in inches.
    """
    return cls_interp(flow_rate, width, height)

def circular_scupper_dh(flow_rate, diameter):
    """
    Calculates the interpolated hydraulic head (in inches) for the given flow
    rate and scupper opening width, based on ASCE Table C8.3-5.

    Parameters
    ----------
    flow_rate : float or int
        The flow rate to the scupper in gal/min
    diameter : float or int
        The diameter of the scupper opening in inches.
    """
    return cls_interp(flow_rate, diameter)

def calc_flow_rate(drainage_area, rainfall_intensity):
    """
    Calculates the flow rate in gal/min to a given scupper based on ASCE
    Eq. C8.3-1.

    Parameters
    ----------
    drainage_area : float or int
        The roof area drained by the scupper in square feet.
    rainfall_intensity : float or int
        The rainfall intensity in inches/hour.
    """
    return 0.0104*float(drainage_area)*float(rainfall_intensity)


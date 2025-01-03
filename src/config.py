from dataclasses import dataclass
from typing import List

@dataclass
class Config:
    """
    Configuration class for networthdash.
    
    Parameters
    ----------
    csv : str
        Path and filename of the CSV input file.
    savedir : str
        Path (ending in "/") to save PDF dashboards.
    datefmt : str
        The date format used in the CSV file.
    since_yr : int, optional
        Year to start the dashboard (default is the earliest year in the CSV file).
    born_yr : int
        The year you were born.
    retire_age : int
        The age at which you expect to retire.
    income_thresh : float
        Threshold (between 0 and 1) for identifying "major" or "minor" income sources 
        based on the all-time grand totals for each income column.
    linear_window : float
        Number of years to linearly extrapolate from.
    anon : bool
        If True, hides all numerical labels.
    """
    
    csv: str = "net-worth.csv"
    savedir: str = "Net worth/"
    datefmt = '%Y/%m/%d'
    
    since_yr: int = None

    born_yr: int = None
    retire_age: int = 67
    
    income_thresh: float = 0.8
    linear_window: float = 1
    
    anon: bool = False


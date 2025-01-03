from dataclasses import dataclass
from typing import List

@dataclass
class Config:
    """
    Configuration class for networthdash
    
    Attributes:
        csv (str): path and filename of CSV input file

        savedir (str): path (ending in "/") to save PDF dashboards to

        datefmt (str): the date format of dates used in the CSV file
        
        since_yr (int): year to start the dashboard (defaults to earliest year in CSV file)
        
        born_yr (int): year you were born

        retire_age (int): year you expect to retire
        
        income_thresh (float): threshold between zero and one to identify "major" or "minor" income sources based on the all-time grand totals for each income column.
        
        linear_window (float): number of years to linearly extrapolate from
        
        anon (bool): if True, hides all numerical labels
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


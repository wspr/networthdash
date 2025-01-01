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
        
        cash_cols (List[str]): columns which contain cash entries
        super_cols (List[str]): columns which contain super entries
        shares_cols (List[str]): columns which contain shares entries
        income_major (List[str]): columns which contain "major" income entries
        income_minor (List[str]): columns which contain "minor" income entries
    """
    
    csv: str = "net-worth.csv"
    savedir: str = "Net worth/"
    datefmt = '%Y/%m/%d'
    
    since_yr: int = None
    born_yr: int = None
    retire_age: int = 67
    
    income_minor: List[str] = ("Interest","Dividend")
    income_major: List[str] = ("Pay")
    
    cash_cols: List[str] = ("Active","Savings")
    shares_cols: List[str] = ("Shares")
    super_cols: List[str] = ("Super")


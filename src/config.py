from dataclasses import dataclass

@dataclass
class Config:
    """
    Configuration class for networthdash
    
    Attributes:
        csv (str): path and filename of CSV input file
        savedir (str): path (ending in "/") to save PDF dashboards to
    """
    
    csv: str = "net-worth.csv"
    savedir: str = "Net worth/"


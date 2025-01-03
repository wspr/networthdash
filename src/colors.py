from dataclasses import dataclass
from typing import List

@dataclass
class Colors:
    """
    Color class for networthdash.
    
    Parameters
    ----------
    bg : str
        Background colour of the figure.
    axis : str
        Background colour of the axes.
    text : str
        Colour of generic text.
    label : str
        Colour of text labels.
    title : str
        Colour of axis titles.
    tick : str
        Colour of axis ticks.
    dashes : str
        Colour of dashed lines.
    frame : str
        Colour of axis frames.
    grid : str
        Colour of axis grids.
    target : str
        Colour of extrapolated target intersection lines.
    lines : List[str]
        Colour of individual lines. Currently indexed numerically, might change to be a dict later. 
    """

    bg: str = "#272727"
    axis: str = "#4e4e4e"
    text: str = "white"
    label: str = "white"
    title: str = "white"
    tick: str = "white"
    dashes: str = "white"
    frame: str = "white"
    grid: str = "#b5b5b5"
    target: str = "#b5b5b5"
    lines = ("#8ec6ff","#ffbf80","#5eff86","#ffa1a1","#e9a8ff")


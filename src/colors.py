from dataclasses import dataclass
from typing import List

@dataclass
class Colors:
    """
    Color class for networthdash.
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


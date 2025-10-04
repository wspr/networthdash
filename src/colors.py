from dataclasses import dataclass


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
    contrast : str
        Colour of contrast text (e.g., overlaid percentages on Sankey plots).
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
    super : str
        Colour of Super lines/labels.
    total : str
        Colour of total net worth lines/labels.
    shares : str
        Colour of Shares lines/labels.
    cash : str
        Colour of Cash lines/labels.
    expend : str
        Colour of lines/labels for expenditure on shares investments.
    """

    bg: str = "#272727"
    axis: str = "#4e4e4e"
    text: str = "white"
    contrast: str = "black"
    label: str = "white"
    title: str = "white"
    tick: str = "white"
    dashes: str = "white"
    frame: str = "white"
    grid: str = "#b5b5b5"
    target: str = "#b5b5b5"
    super: str = "#ffbf80"
    total: str = "#8ec6ff"
    shares: str = "#5eff86"
    cash: str = "#ffa1a1"
    expend: str = "#e9a8ff"
    income: str = "#e3a3aa"

    def __getitem__(self, key: str) -> str:
        return getattr(self, key)

    # allows colors["bg"] for instance

from dataclasses import dataclass, field

from .colors import Colors
from .strings import Strings


@dataclass
class Config:
    """
    Configuration class for networthdash.

    Parameters
    ----------
    csv : str
        Filename of the CSV input file. Path information should not be included.
    csvdir : str
        Path to the CSV input file. Concatenated directly with the CSV filename, so should end in a "/".
    savedir : str
        Path (ending in "/") to save PDF dashboards.
    saveprefix : str
        First part of filename to save. Defaults to the CSV filename stripped of its file extension.
    savesuffix : str
        Second part of the filename is a date stamp specified in standard datetime format (e.g., `%Y-%m-%d`). Default setting omits the day, assuming you don't need to log updates too often.
    savepdf : bool
        If true saves a PDF of the dashboard in the `savedir` folder.
    savejpg : bool
        If true saves a JPG of the dashboard in the `savedir` folder.
    savepng : bool
        If true saves a PNG of the dashboard in the `savedir` folder.
    datefmt : str
        The date format used in the CSV file.
    since_yr : int
        Year to start the dashboard (default is the earliest year in the CSV file).
    until_yr : int
        Year to conclude the dashboard (default is the latest year in the CSV file).
    born_yr : int
        The year you were born.
    retire_age : int
        The age at which you expect to retire.
    retire_ratio : float
        Thw fraction of your net worth to commence drawing down from yearly in retirement (e.g., for the "4% rule" it would be 0.04).
    cash_thresh : float
        Threshold (between 0 and 1) for identifying "major" or "minor" cash sources based on the all-time grand totals for each cash column.
    income_thresh : float
        Threshold (between 0 and 1) for identifying "major" or "minor" income sources based on the all-time grand totals for each income column.
    linear_window : float
        Number of years before the current date to linearly extrapolate from.
    future_window : float
        The maximum number of extrapolation years to show on the graph.
    linear_targets: list[float]
        "Targets" to extrapolate to linearly to gauge time until net worth milestones.
    anon : bool
        If True, hides all numerical labels.
    colors : Colors
        Colors class setup for plot colours. See Colors class for defaults and options.
    strings : Strings
        Strings class setup for dashboard strings. Includes strings used in the CSV file. See Strings class for defaults and options.
    figw : float
        Plot size, horizontal width (physical size).
    figh : float
        Plot size, vertical height (physical size).
    linewidth : float
        Linewidth of scatter plots.
    marker : str
        Marker of scatter plots.
    markersize : float
        Markersize of scatter plots.
    node_width : float
        Relative width of Sankey diagram nodes (ausankey parameter).
    node_alpha : float
        Alpha (transparency) of Sankey diagram nodes (ausankey parameter).
    flow_alpha : float
        Alpha (transparency) of Sankey diagram flow transitions between nodes (ausankey parameter).
    currency_sign : str
        The currency sign used to display amounts.
    sankey_sort : str
        The sort option to pass through to the Sankey diagrams. Valid options are `"top"`, `"bottom"`, `"none"`.
    sankey_colormaps : list
        Three colormaps for the panels which are automatically coloured based on breakdown of components. (I.e., not coloured using the Colors class.)
    """

    born_yr: int

    csv: str = "net-worth.csv"
    csvdir: str = "./"
    datefmt: str = "%Y/%m/%d"

    savedir: str = "Net worth archive/"
    saveprefix: str = None
    savesuffix: str = "%Y-%m"

    savepdf: bool = True
    savejpg: bool = False
    savepng: bool = False

    since_yr: int = None
    until_yr: int = None
    retire_age: int = 67
    retire_ratio: float = 0.04

    # cash_thresh: float = 0.6
    income_thresh: float = 0.6
    linear_window: float = 1.0
    future_window: int = 8

    anon: bool = False

    figw: float = 6
    figh: float = 12.5

    linewidth: float = 1.0
    markersize: float = 4.0
    marker: str = "."

    colors: "Colors" = field(default_factory=Colors)

    strings: "Strings" = field(default_factory=Strings)

    node_width: float = 0.15
    node_alpha: float = 0.8
    flow_alpha: float = 0.5

    currencysign = "$"

    sankey_sort: str = "bottom"
    sankey_colormaps: list = ("Set3", "Pastel1", "Pastel2")

    linear_targets: list[float] = (
        5000,
        10000,
        15000,
        20000,
        35000,
        50000,
        75000,
        100000,
        150000,
        200000,
        350000,
        500000,
        750000,
        1000000,
        1500000,
        2000000,
        3500000,
        5000000,
        7500000,
        10000000,
        20000000,
        50000000,
        100000000,
    )

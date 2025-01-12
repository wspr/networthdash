from dataclasses import dataclass


@dataclass
class Strings:
    """
    Strings class for networthdash.

    Parameters
    ----------
    datecol : str
        Name of the column "Date".
    """

    datecol: str = "Date"

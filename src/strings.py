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
    supercol: str = "Super"
    sharescol: str = "Shares"
    cashcol: str = "Cash"
    incomecol: str = "Income"
    expendcol: str = "Expend"

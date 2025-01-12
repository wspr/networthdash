import networthdash as nwd
import unittest

class GenericTest(unittest.TestCase):

    """Generic tests for nwd."""

    def test_simple(self):
        cfg = nwd.Config(
            csv = "nwd_example.csv" ,
            saveprefix = "test_simple"
            datefmt = "%Y-%m-%d",
            born_yr = 1981 ,
            retire_age = 67 ,
        )
        nwd.dashboard(cfg)


import pytest
import src as nwd 
# recall we are within the repo when running the test

std = {
    "csvdir": "tests/" ,
    "datefmt": "%Y-%m-%d" ,
    "born_yr": 1981 ,
    "retire_age": 67 ,
    "savepdf": False ,
}


@pytest.mark.parameterize("csvname",[
    "nwd_example",
    "nwd_example_nosuper",
    "nwd_example_nocash",
    "nwd_example_noshares",
])
@pytest.mark.parameterize("anon",[True, False])
def test_simple(csvname,anon):
    cfg = nwd.Config(**std ,
        csv = csvname + ".csv" ,
        anon = anon ,
    )
    nwd.dashboard(cfg)


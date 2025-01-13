import src as nwd 
# recall we are within the repo when running the test

std = {
    "csvdir": "tests/" ,
    "datefmt": "%Y-%m-%d" ,
    "born_yr": 1981 ,
    "retire_age": 67 ,
    "savepdf": False ,
}

def test_simple():
    cfg = nwd.Config(**std ,
        csv = "nwd_example.csv" ,
    )
    nwd.dashboard(cfg)

def test_nosuper():
    cfg = nwd.Config(**std ,
        csv = "nwd_example_nosuper.csv" ,
    )
    nwd.dashboard(cfg)


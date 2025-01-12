import src as nwd 
# recall we are within the repo when running the test

def test_simple():
    cfg = nwd.Config(
        csv = "nwd_example.csv" ,
        saveprefix = "test_simple" ,
        datefmt = "%Y-%m-%d" ,
        born_yr = 1981 ,
        retire_age = 67 ,
    )
    nwd.dashboard(cfg)



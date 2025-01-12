import src as nwd 
# recall we are within the repo when running the test

def test_simple():
    cfg = nwd.Config(
        csv = "nwd_example.csv" ,
        csvdir = "tests/" ,
        saveprefix = "test_simple" ,
        savedir = "_site/" ,
        datefmt = "%Y-%m-%d" ,
        born_yr = 1981 ,
        retire_age = 67 ,
        savepng = True ,
        savepdf = False ,
    )
    nwd.dashboard(cfg)



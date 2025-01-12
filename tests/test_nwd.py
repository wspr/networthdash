import networthdash as nwd 
# recall we are within the repo when running the test

print(dir(nwd))

def test_simple():
    cfg = nwd.Config(
        csv = "nwd_example.csv" ,
        csvdir = "tests/" ,
        saveprefix = "test_simple" ,
        datefmt = "%Y-%m-%d" ,
        born_yr = 1981 ,
        retire_age = 67 ,
        savepdf = False ,
    )
    nwd.dashboard(cfg)



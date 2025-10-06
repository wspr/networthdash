import networthdash as nwd

cfg = nwd.Config(
    csv="nwd_example.csv",
    datefmt="%Y-%m-%d",
    born_yr=1981,
    retire_age=67,
)

nwd.dashboard(cfg)

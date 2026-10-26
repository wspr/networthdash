import pytest

import src as nwd

# recall we are within the repo when running the test

std = {
    "csvdir": "tests/",
    "datefmt": "%Y-%m-%d",
    "born_yr": 1981,
    "retire_age": 67,
    "savepdf": False,
}


@pytest.mark.parametrize(
    "csvname",
    [
        "nwd_example",
        "nwd_example_nosuper",
        "nwd_example_nocash",
        "nwd_example_noshares",
        "nwd_example_noexpend",
        "nwd_example_noincome",
        "nwd_example_nominor",
    ],
)
@pytest.mark.parametrize("anon", [True, False])
def test_simple(csvname, anon):
    cfg = nwd.Config(
        **std,
        csv=csvname + ".csv",
        anon=anon,
    )
    nwd.dashboard(cfg)


@pytest.mark.parametrize("fund", ["VDHG", "VAS"])
@pytest.mark.parametrize("anon", [True, False])
def test_share4(fund, anon):
    cfg = nwd.Config(
        **std,
        csv="nwd_example_share.csv",
        anon=anon,
        layout="share4",
    )
    cfg.share_focus = {"expend_col": "Stake", "fund": fund}
    nwd.dashboard(cfg)

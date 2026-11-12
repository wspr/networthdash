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


def test_fund_irr():
    import pandas as pd

    from src.main import fund_irr

    # $100 in at the start, worth $110 a year later: 10% p.a.
    data = pd.DataFrame({"Days": [0.0, 1.0], "spend": [100, 0], "val": [100, 110]})
    assert fund_irr(data, "val", "spend") == pytest.approx(0.10, abs=1e-6)

    # plus a $5 dividend at the end: 15% p.a.
    data["div"] = [0, 5]
    assert fund_irr(data, "val", "spend", "div") == pytest.approx(0.15, abs=1e-6)

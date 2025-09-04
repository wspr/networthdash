import os
from datetime import datetime, timezone

import ausankey as sky
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import AutoMinorLocator

from .config import Config

####################


def dashboard(config: Config):
    # internal parameters
    # (possibly to generalise later)

    config.expstart = 0

    config.label_path_effects = {
        "linewidth": 1,
        "foreground": config.colors.contrast,
    }

    ############# HELPERS

    config.errors = {}
    config.errors["DateColMissing"] = f"One column must be called '{config.strings.datecol}'."

    config.dotstyle = {
        "marker": config.marker,
        "markersize": config.markersize,
        "linestyle": "None",
    }

    config.projstyle = {
        "linestyle": "-",
        "marker": "None",
        "linewidth": config.linewidth / 4,
    }

    config = read_headers(config)

    ############# DATA

    alldata = pd.read_csv(config.csvdir + config.csv, header=1).fillna(0)
    alldata.columns = list(config.hdrnew.keys())
    alldata["Year"] = dates_to_years(config, alldata)
    alldata[config.expend_cols] = alldata[config.expend_cols].applymap(parse_purchase)
    alldata[config.cash_cols] = alldata[config.cash_cols].applymap(parse_purchase)

    config.retire_yr = config.born_yr + config.retire_age
    ahead_yr = datetime.now(timezone.utc).year + config.future_window
    config.max_yr = min(ahead_yr, config.retire_yr)

    config.since_yr = config.since_yr or min(alldata.Year)
    config.until_yr = config.until_yr or max(alldata.Year)
    config.years_until_retire = config.max_yr - config.since_yr
    config.age_at_retire = config.max_yr - config.born_yr

    alldata["Days"] = dates_to_days(config, alldata)
    alldata["TotalSuper"] = alldata[config.super_cols].sum(axis=1)
    alldata["TotalShares"] = alldata[config.shares_cols].sum(axis=1)
    alldata["TotalCash"] = alldata[config.cash_cols].sum(axis=1)
    alldata["TotalExpend"] = alldata[config.expend_cols].sum(axis=1)
    alldata["TotalIncome"] = alldata[config.income_cols].sum(axis=1)
    alldata["Total"] = alldata["TotalShares"] + alldata["TotalSuper"] + alldata["TotalCash"]

    alldata = alldata.sort_values(by="Days").reset_index(drop=True)
    income_grand_tot = alldata["TotalIncome"].sum()
    income_sum = alldata[config.income_cols].sum()
    config.income_minor = list(income_sum[income_sum < (1 - config.income_thresh) * income_grand_tot].keys())
    config.iminor_bool = len(config.income_minor) > 0

    ## not currently used in the cash panel but this should be generalised
    # cash_grand_tot = alldata["TotalCash"].sum()
    # cash_sum = alldata[config.cash_cols].sum()
    # config.cash_minor = list(cash_sum[cash_sum < (1 - config.cash_thresh) * cash_grand_tot].keys())
    # config.cminor_bool = len(config.cash_minor) > 0

    config.years_uniq = {}
    for x in alldata["Year"]:
        if x >= config.since_yr and x <= config.until_yr:
            config.years_uniq[x] = True

    ########### CREATE FIGURE and AXES

    if isinstance(config.layout, str):
        config.layout = [config.layout]

    if "main7" in config.layout:
        create_dashboard_main7(config, alldata)

    if "plain8" in config.layout:
        create_dashboard_plain8(config, alldata)


def create_dashboard_main7(config, alldata):
    data = alldata[alldata.Total > 0].reset_index(drop=True)
    config.window_ind = data.Days > (data.Days.iat[-1] - config.linear_window)

    # Calculate expenditure
    if config.expend_bool:
        data_sp = alldata[alldata.TotalExpend > 0].reset_index(drop=True)
        config.win_sp_ind = data_sp.Days > (data_sp.Days.iat[-1] - config.linear_window)
    else:
        data_sp = alldata  # dummy data, not used, to ensure variable exists

    main_wd = 0.75
    main_ht = 0.30
    pane_w = 0.35
    pane_h = 0.15
    sankey_w = 0.375
    sankey_h = 0.15

    pane_x = [0.1, 0.55]
    row_y = [0.04, 0.43, 0.78]
    row_gap = 0.03

    inset_w = 0.25
    inset_h = 0.11
    inset_x = pane_x[0] + 0.15
    inset_y = row_y[1] + main_ht / 2 + 0.025

    fig, ax0 = plt.subplots(
        figsize=(config.figw, config.figh),
        facecolor=config.colors.bg,
    )
    ax0.axis("off")

    ax00 = fig.add_axes([0.02, 0.93, 0.96, 0.05])

    ax1 = fig.add_axes([(1 - main_wd) / 2, row_y[1], main_wd, main_ht])
    ax2 = fig.add_axes([pane_x[0], row_y[2], pane_w, pane_h])
    ax3 = fig.add_axes([pane_x[1], row_y[2], pane_w, pane_h])

    ax4 = fig.add_axes([pane_x[0], row_gap + row_y[0] + sankey_h, sankey_w, sankey_h])
    ax5 = fig.add_axes([pane_x[1] - 0.02, row_gap + row_y[0] + sankey_h, sankey_w, sankey_h])

    ax6 = fig.add_axes([pane_x[0], row_y[0], sankey_w, sankey_h])
    ax7 = fig.add_axes([pane_x[1] - 0.02, row_y[0], sankey_w, sankey_h])

    ax8 = fig.add_axes([inset_x, inset_y, inset_w, inset_h])

    if config.expend_bool:
        ax33 = ax3.twinx()
        color_axes(config, ax33)
        ax33.tick_params(axis="y", labelcolor=config.colors.expend)
    else:
        ax33 = ax3
    ######## PANELS ########

    panel_timeline(config, ax00)
    # Calculate expenditure
    if config.expend_bool:
        data_sp = alldata[alldata.TotalExpend > 0].reset_index(drop=True)
        config.win_sp_ind = data_sp.Days > (data_sp.Days.iat[-1] - config.linear_window)
    else:
        data_sp = alldata  # dummy data, not used, to ensure variable exists

    panel_all_vs_time(config, ax1, data)
    panel_total_window(config, ax8, data)

    xx = ax8.get_xlim()
    yy = ax8.get_ylim()
    xp = pd.Series([xx[1], xx[0], xx[0], xx[1]])
    yp = pd.Series([yy[1], yy[1], yy[0], yy[0]])
    ax1.plot(xp, yp, color=config.colors.frame)

    panel_cash_window_percent(config, ax2, data)

    config.profitloss = panel_shares_window(config, ax3, ax33, data, data_sp)

    ######## PANEL 4-5 ########

    panel_income(config, ax4, alldata)
    panel_shares(config, ax5, alldata)
    if config.income_bool and config.shares_bool:
        yticks_equalise(config, ax4, ax5)

    if config.income_bool:
        faux_title(config, ax4, "Annual income")

    if not config.shares_bool:
        pass
    elif config.anon or (not config.expend_bool):
        faux_title(config, ax5, "Annual shares increase")
    else:
        faux_title(
            config, ax5, "Annual shares increase\nAll-time profit = " + int_to_dollars(config, config.profitloss)
        )

    ######## PANEL 6-7 ########

    panel_income_breakdown(config, alldata, ax6)
    panel_shares_breakdown(config, data, ax7)

    ############## FINISH UP

    plt.show()
    savefiles(config, fig)
    plt.close()


def create_dashboard_plain8(config, alldata):
    data = alldata[alldata.Total > 0].reset_index(drop=True)
    config.window_ind = data.Days > (data.Days.iat[-1] - config.linear_window)

    # Calculate expenditure
    if config.expend_bool:
        data_sp = alldata[alldata.TotalExpend > 0].reset_index(drop=True)
        config.win_sp_ind = data_sp.Days > (data_sp.Days.iat[-1] - config.linear_window)
    else:
        data_sp = alldata  # dummy data, not used, to ensure variable exists
    pane_w = 0.35
    pane_h = 0.15
    sankey_w = 0.375
    sankey_h = 0.15

    pane_x = [0.1, 0.55]
    row_y = [0.1, 0.3, 0.5, 0.7]

    fig, ax0 = plt.subplots(
        figsize=(config.figw, config.figh),
        facecolor=config.colors.bg,
    )
    ax0.axis("off")

    ax00 = fig.add_axes([0.02, 0.93, 0.96, 0.05])

    ax1 = fig.add_axes([pane_x[0], row_y[0], pane_w, pane_h])
    ax2 = fig.add_axes([pane_x[0], row_y[1], pane_w, pane_h])
    ax3 = fig.add_axes([pane_x[0], row_y[2], pane_w, pane_h])
    ax4 = fig.add_axes([pane_x[0], row_y[3], pane_w, pane_h])

    ax5 = fig.add_axes([pane_x[1], row_y[0], sankey_w, sankey_h])
    ax6 = fig.add_axes([pane_x[1], row_y[1], sankey_w, sankey_h])
    ax7 = fig.add_axes([pane_x[1], row_y[2], sankey_w, sankey_h])
    ax8 = fig.add_axes([pane_x[1], row_y[3], sankey_w, sankey_h])

    if config.expend_bool:
        ax33 = ax3.twinx()
        color_axes(config, ax33)
        ax33.tick_params(axis="y", labelcolor=config.colors.expend)
    else:
        ax33 = ax3

    ######## PANELS ########

    panel_timeline(config, ax00)

    panel_total_window(config, ax4, data)
    panel_shares_window(config, ax3, ax33, data, data_sp)
    panel_super_window(config, ax2, data)
    panel_cash_window(config, ax1, data)

    panel_cash_breakdown(config, data, ax5)
    panel_super_breakdown(config, data, ax6)
    panel_shares_breakdown(config, data, ax7)

    ############## FINISH UP

    plt.show()
    plt.close()

    ############ SUBFUNCTIONS
    panel_total_window(config, ax8, data)

    xx = ax8.get_xlim()
    yy = ax8.get_ylim()
    xp = pd.Series([xx[1], xx[0], xx[0], xx[1]])
    yp = pd.Series([yy[1], yy[1], yy[0], yy[0]])
    ax1.plot(xp, yp, color=config.colors.frame)

    panel_cash_window_percent(config, ax2, data)

    config.profitloss = panel_shares_window(config, ax3, ax33, data, data_sp)

    ######## PANEL 4-5 ########

    panel_income(config, ax4, alldata)
    panel_shares(config, ax5, alldata)
    if config.income_bool and config.shares_bool:
        yticks_equalise(config, ax4, ax5)

    if config.income_bool:
        faux_title(config, ax4, "Annual income")

    if not config.shares_bool:
        pass
    elif config.anon or (not config.expend_bool):
        faux_title(config, ax5, "Annual shares increase")
    else:
        faux_title(
            config, ax5, "Annual shares increase\nAll-time profit = " + int_to_dollars(config, config.profitloss)
        )

    ######## PANEL 6-7 ########

    panel_income_breakdown(config, alldata, ax6)
    panel_shares_breakdown(config, data, ax7)

    ############## FINISH UP

    plt.show()
    savefiles(config, fig)
    plt.close()


############ SUBFUNCTIONS


def read_headers(config):
    datecol = config.strings.datecol

    hdr = pd.read_csv(config.csvdir + config.csv, header=None, nrows=2).transpose()

    hdrnew = {}
    for ii, _ in enumerate(hdr[1]):
        prefix = hdr[0][ii] if isinstance(hdr[0][ii], str) else "_"
        tmpstr = datecol if hdr[1][ii] == datecol else prefix + "_" + hdr[1][ii]
        hdrnew[tmpstr] = hdr[1][ii]

    hdr[1] = list(hdrnew.keys())

    config.super_cols = list(hdr[1][hdr[0] == config.strings.supercol])
    config.shares_cols = list(hdr[1][hdr[0] == config.strings.sharescol])
    config.cash_cols = list(hdr[1][hdr[0] == config.strings.cashcol])
    config.expend_cols = list(hdr[1][hdr[0] == config.strings.expendcol])
    config.income_cols = list(hdr[1][hdr[0] == config.strings.incomecol])

    config.super_bool = len(config.super_cols) > 0
    config.shares_bool = len(config.shares_cols) > 0
    config.cash_bool = len(config.cash_cols) > 0
    config.expend_bool = len(config.expend_cols) > 0
    config.income_bool = len(config.income_cols) > 0

    config.hdrnew = hdrnew

    return config


def savefiles(config, fig):
    saveprefix = config.saveprefix or os.path.splitext(config.csv)[0]
    filename = config.savedir + saveprefix + "-" + datetime.now(timezone.utc).strftime(config.savesuffix)

    if config.anon:
        filename = filename + "-anon"

    if config.savepdf or config.savepng or config.savejpg:
        os.makedirs(config.savedir, exist_ok=True)

    if config.savepdf:
        fig.savefig(filename + ".pdf")
    if config.savejpg:
        fig.savefig(filename + ".jpg")
    if config.savepng:
        fig.savefig(filename + ".png")


def dates_to_years(config, alldata):
    datecol = config.strings.datecol
    allcols = alldata.columns.tolist()
    if datecol not in allcols:
        raise RuntimeError(config.errors.DateColMissing)

    return alldata[datecol].apply(lambda x: datetime.strptime(x, config.datefmt).replace(tzinfo=timezone.utc).year)


def dates_to_days(config, data):
    datecol = config.strings.datecol
    sincedate = datetime(config.since_yr, 1, 1, tzinfo=timezone.utc)
    days = np.empty(len(data[datecol]))
    for ii, ent in enumerate(data[datecol]):
        y = datetime.strptime(ent, config.datefmt).replace(tzinfo=timezone.utc)
        days[ii] = (y - sincedate).days / 365
    return days


# from Claude:
def parse_purchase(value):
    try:
        # Handle math expressions like "20 x 4 + 10"
        if any(op in value for op in ["x", "+", "-", "*"]):
            # Replace 'x' with '*' for Python and clean up
            expr = value.replace("x", "*").replace("$", "").strip()

            # Simple arithmetic parser for basic expressions
            # Split by + and - first (lowest precedence)
            current = ""
            sign = 1
            total = 0

            i = 0
            while i < len(expr):
                if expr[i] in "+-":
                    if current.strip():
                        total += sign * _evaluate_multiply_divide(current.strip())
                        current = ""
                    sign = 1 if expr[i] == "+" else -1
                else:
                    current += expr[i]
                i += 1

            if current.strip():
                total += sign * _evaluate_multiply_divide(current.strip())

            return total
        # Simple number
        return float(value.replace("$", ""))
    except (ValueError, TypeError):
        return float(value)


def _evaluate_multiply_divide(expr):
    """Helper function to evaluate multiplication and division."""
    # Handle multiplication only for now (as the example uses 'x')
    if "*" in expr:
        parts = expr.split("*")
        result = 1.0
        for part in parts:
            result *= float(part.strip())
        return result
    return float(expr)


############## MINI PANEL: Timeline


def panel_timeline(config, ax):
    color_axes(config, ax)
    ax.axis("off")
    # Get today's date
    now = datetime.now(timezone.utc)

    # First and last day of the year
    start_of_year = datetime(now.year, 1, 1, tzinfo=timezone.utc)
    end_of_year = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)

    # Total seconds in the year and seconds passed
    year_duration = (end_of_year - start_of_year).total_seconds()
    elapsed = (now - start_of_year).total_seconds()

    # Calculate percentage
    percentage = elapsed / year_duration
    xx = percentage

    ax.plot([0, 1], [1, 1], "-", color=config.colors.frame)

    npoints = 26
    edgecol = config.colors.frame
    for ii in range(npoints):
        jj = ii / (npoints - 1)
        facecol = config.colors.frame
        if jj > percentage:
            facecol = config.colors.bg

        ax.plot(
            [jj],
            [1],
            "o",
            markeredgecolor=edgecol,
            markerfacecolor=facecol,
        )

    ax.plot(
        [xx],
        [1],
        "o",
        markeredgecolor=edgecol,
        markerfacecolor=config.colors.total,
    )
    ax.set_xlim([-0.01, 1.01])
    ax.set_ylim([0, 2])


############## PANEL 1: All vs Time


def panel_all_vs_time(config, ax, data):
    color_axes(config, ax)
    ax.set_title("", color=config.colors.title)
    ax.axvline(x=data.Days.iat[-1], linestyle="--", color=config.colors.dashes)

    if config.retire_yr == config.max_yr:
        ax.axvline(x=config.retire_yr - config.since_yr, linestyle="--", color=config.colors.dashes)

    def extrap(d, t):
        reg = np.polyfit(d, t, 1)
        rd = np.linspace(data.Days[config.window_ind].iat[0], config.years_until_retire)
        yd = rd * reg[0] + reg[1]
        return rd, yd

    def extrap_exp(ax, d, t, arg):
        clim = ax.get_ylim()
        logfit = np.polyfit(d, np.log(t), 1, w=np.sqrt(t))
        rd = np.linspace(d.iloc[0], config.years_until_retire)
        yd = np.exp(logfit[1]) * np.exp(logfit[0] * rd)
        infl = np.exp(logfit[0]) - 1
        ax.plot(rd, yd, **(config.projstyle | arg))
        ax.set_ylim(clim)
        return infl

    # total line
    rd1, yd1 = extrap(data.Days[config.window_ind], data.Total[config.window_ind])
    retire_worth = yd1[-1]
    ax.plot(rd1, yd1, **config.projstyle, color=config.colors.total)
    extrap_exp(ax, data.Days[config.expstart : -1], data.Total[config.expstart : -1], {"color": config.colors.total})

    ax.plot(data.Days, data.Total, color=config.colors.total, **config.dotstyle)

    # super
    if config.super_bool:
        rd2, yd2 = extrap(data.Days[config.window_ind], data.TotalSuper[config.window_ind])
        ax.plot(rd2, yd2, **config.projstyle, color=config.colors.super)

        ind = data.TotalSuper[config.expstart : -1] > 0
        days = data.Days[config.expstart : -1][ind]
        val = data.TotalSuper[config.expstart : -1][ind]
        extrap_exp(ax, days, val, {"color": config.colors.super})

        ax.plot(data.Days, data.TotalSuper, color=config.colors.super, **config.dotstyle)

    if config.shares_bool:
        rd3, yd3 = extrap(data.Days[config.window_ind], data.TotalShares[config.window_ind])
        ax.plot(rd3, yd3, **config.projstyle, color=config.colors.shares)

        ind = data["TotalShares"][config.expstart : -1] > 0
        days = data.Days[config.expstart : -1][ind]
        val = data["TotalShares"][config.expstart : -1][ind]
        extrap_exp(ax, days, val, {"color": config.colors.shares})

        ax.plot(data.Days, data["TotalShares"], color=config.colors.shares, **config.dotstyle)

    if config.cash_bool:
        ax.plot(data.Days, data["TotalCash"], **config.dotstyle, color=config.colors.cash)

    ############% LABELS

    va = "center"

    if config.cash_bool:
        ax.text(data.Days.iat[-1], data["TotalCash"].iat[-1], "  Cash", color=config.colors.cash, va=va)

    if config.shares_bool:
        ax.text(data.Days.iat[-1], data["TotalShares"].iat[-1], "  Shares", color=config.colors.shares, va=va)

    if config.super_bool:
        ax.text(data.Days.iat[-1], data["TotalSuper"].iat[-1], "  Super", color=config.colors.super, va=va)

    ax.text(data.Days.iat[-1], data.Total.iat[-1], "  Total", va="center", color=config.colors.total)

    ax.set_xticks(range(config.years_until_retire + 1))
    ax.set_xticklabels(
        range(config.since_yr, config.since_yr + config.years_until_retire + 1), rotation=90, color=config.colors.tick
    )
    clim = ax.get_ylim()
    ax.set_ylim(0, clim[1])
    yticks_dollars(config, ax)
    ax.set_ylim(0, clim[1])

    if not config.anon:
        txtstr = (
            f"{config.retire_ratio:.1%} rule\n= " f"{int_to_dollars(config, config.retire_ratio*retire_worth)}" f"/yr"
        )
        ax.text(
            0.98 * rd1[-1],
            0.95 * retire_worth,
            f"Age {config.age_at_retire}\n" + txtstr,
            color=config.colors.total,
            ha="right",
            va="top",
            backgroundcolor=config.colors.axis,
        )
        ax.plot(
            rd1[-1],
            retire_worth,
            marker="+",
            markersize=config.markersize,
            color=config.colors.total,
        )

        def extra_ticks(config, ax, ticks, col):
            axx1 = ax.twinx()
            color_axes(config, axx1)
            axx1.set_ylim(0, clim[1])
            axx1.set_yticks(ticks)
            axx1.tick_params(
                axis="y",
                direction="out",
                right=True,
                left=False,
                labelcolor=col,
            )
            yticks_dollars(config, axx1)

        extra_ticks(config, ax, [data.Total.iat[-1], retire_worth], config.colors.total)
        if config.cash_bool:
            extra_ticks(config, ax, [data.TotalCash.iat[-1]], config.colors.cash)
        if config.shares_bool:
            extra_ticks(config, ax, [data.TotalShares.iat[-1]], config.colors.shares)
        if config.super_bool:
            extra_ticks(config, ax, [data.TotalSuper.iat[-1]], config.colors.super)

    if config.anon:
        ax.set_yticklabels([])
        ax.set_ylabel("Amount", color=config.colors.text)

    #######%%###### EXTRAP

    def extrap_target(yy):
        if data.Total.iat[-1] > 0.8 * yy:
            return

        reg = np.polyfit(data.Days[config.window_ind], data.Total[config.window_ind], 1)

        rr = (yy - reg[1]) / reg[0]

        ax.plot((rr, rr, data.Days.iat[-1]), (0, yy, yy), "-", lw=config.linewidth, color=config.colors.target)

        ax.text(
            data.Days.iat[-1] + (rr - data.Days.iat[-1]) / 2,
            yy * 0.99,
            f"{round(rr-data.Days.iat[-1],1)} yrs",
            ha="center",
            va="top",
            color=config.colors.text,
        )
        ax.text(
            data.Days.iat[-1] + (rr - data.Days.iat[-1]) / 2,
            yy * 1.01,
            int_to_dollars(config, yy),
            ha="center",
            va="bottom",
            color=config.colors.text,
        )

    if not config.anon:
        for ii in config.linear_targets:
            if ii < 0.85 * ax.get_ylim()[1]:
                extrap_target(ii)


def panel_total_window(config, ax, data):
    color_axes(config, ax)

    reg = np.polyfit(data.Days[config.window_ind], data.Total[config.window_ind], 1)
    rd = np.linspace(data.Days[config.window_ind].iat[0], data.Days.iat[-1])
    yd = rd * reg[0] + reg[1]
    ax.plot(rd, yd, "-", lw=config.linewidth / 4, color=config.colors.total)
    ax.plot(data.Days[config.window_ind], data.Total[config.window_ind], color=config.colors.total, **config.dotstyle)

    logfit = np.polyfit(
        data.Days[config.window_ind], np.log(data.Total[config.window_ind]), 1, w=np.sqrt(data.Total[config.window_ind])
    )
    rd = np.linspace(data.Days[config.window_ind].iat[0], data.Days.iat[-1])
    yd = np.exp(logfit[1]) * np.exp(logfit[0] * rd)
    infl = np.exp(logfit[0]) - 1
    ax.plot(rd, yd, "--", lw=config.linewidth / 4, color=config.colors.total)

    yticks_dollars(config, ax)

    ax.xaxis.set_minor_locator(AutoMinorLocator(3))
    ax.grid(which="major", color=config.colors.grid, linestyle="-", linewidth=0.5)
    ax.grid(which="minor", color=config.colors.grid, linestyle="-", linewidth=0.5)

    gain = data.Total[config.window_ind].iat[-1] - data.Total[config.window_ind].iat[0]
    elap = data.Days[config.window_ind].iat[-1] - data.Days[config.window_ind].iat[0]

    ax.set_xticklabels([])
    ax.tick_params(axis="y", labelcolor=config.colors.total)

    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    if not config.anon:
        peryrtext = "" if config.linear_window == 1 else ("\n" + int_to_dollars(config, gain / elap) + "/yr")
        txtstr = "Δ=" + int_to_dollars(config, gain) + peryrtext
        ax.text(
            x_min + 0.05 * (x_max - x_min),
            y_min + 0.95 * (y_max - y_min),
            txtstr,
            color=config.colors.total,
            va="top",
            backgroundcolor=config.colors.axis,
        )
        txtstr = f"Exp growth:\n{infl*100:2.1f}% p.a."
        ax.text(
            x_min + 0.95 * (x_max - x_min),
            y_min + 0.05 * (y_max - y_min),
            txtstr,
            color=config.colors.total,
            ha="right",
            va="bottom",
            backgroundcolor=config.colors.axis,
        )

    if config.anon:
        ax.set_yticklabels([])
        ax.set_ylabel("Amount", color=config.colors.text)


def panel_cash_window(config, ax, data):
    color_axes(config, ax)

    if not config.cash_bool:
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        return 0

    ax.plot(
        data.Days[config.window_ind],
        data["TotalCash"][config.window_ind],
        config.marker,
        linestyle="-",
        color=config.colors.cash,
        markersize=config.markersize,
    )

    for col in config.cash_cols:
        ax.plot(
            data.Days[config.window_ind],
            data[col][config.window_ind],
            config.marker,
            linestyle="-",
            #            color=config.colors.cash,
            markersize=config.markersize,
        )

    yticks_dollars(config, ax)
    ax.set_xlabel(f"Years since {config.since_yr}", color=config.colors.label)
    ax.xaxis.set_minor_locator(AutoMinorLocator(3))
    ax.grid(which="major", color=config.colors.grid, linestyle="-", linewidth=0.5)
    ax.grid(which="minor", color=config.colors.grid, linestyle="-", linewidth=0.5)

    faux_title(config, ax, "Cash")
    return None


def panel_cash_window_percent(config, ax, data):
    color_axes(config, ax)

    if not config.cash_bool:
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        return None

    maxcash = max(data["TotalCash"][config.window_ind])
    ax.plot(
        data.Days[config.window_ind],
        data["TotalCash"][config.window_ind] / maxcash,
        config.marker,
        linestyle="-",
        color=config.colors.cash,
        markersize=config.markersize,
    )
    ax.set_ylim([-0.0, 1.1])

    for col in config.cash_cols:
        maxcash = max(data[col][config.window_ind])
        ax.plot(
            data.Days[config.window_ind],
            data[col][config.window_ind] / maxcash,
            config.marker,
            linestyle="-",
            #            color=config.colors.cash,
            markersize=config.markersize,
        )
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(
        ["0%", "20%", "40%", "60%", "80%", "100%"],
        color=config.colors.cash,
    )
    ax.set_xlabel(f"Years since {config.since_yr}", color=config.colors.label)
    ax.xaxis.set_minor_locator(AutoMinorLocator(3))
    ax.grid(which="major", color=config.colors.grid, linestyle="-", linewidth=0.5)
    ax.grid(which="minor", color=config.colors.grid, linestyle="-", linewidth=0.5)

    faux_title(config, ax, "Cash trends")
    return None


def panel_shares_window(config, ax, ax33, data, data_sp):
    color_axes(config, ax)

    if not config.shares_bool:
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax33.set_yticklabels([])
        return 0

    ax.plot(
        data.Days[config.window_ind],
        data["TotalShares"][config.window_ind],
        config.marker,
        color=config.colors.shares,
        markersize=config.markersize,
    )
    ax.set_xlabel(f"Years since {config.since_yr}", color=config.colors.label)

    yticks_dollars(config, ax)
    ax.tick_params(axis="y", labelcolor=config.colors.shares)

    ax.xaxis.set_minor_locator(AutoMinorLocator(3))
    ax.grid(which="major", color=config.colors.grid, linestyle="-", linewidth=0.5)
    ax.grid(which="minor", color=config.colors.grid, linestyle="-", linewidth=0.5)

    shares2 = pd.Series(data["TotalShares"][config.window_ind]).reset_index(drop=True)
    gain = shares2.iat[-1] - shares2.iat[0]
    elap = data.Days[config.window_ind].iat[-1] - data.Days[config.window_ind].iat[0]

    def label_graph_shares_a(ax):
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        if config.anon:
            txt = "Shares\nincrease"
        else:
            peryrtext = "" if config.linear_window == 1 else ("\n" + int_to_dollars(config, gain / elap) + "/yr")
            txt = "Shares\nincrease\n" + int_to_dollars(config, gain) + peryrtext
        ax.text(
            x_min + 0.05 * (x_max - x_min),
            y_min + 0.95 * (y_max - y_min),
            txt,
            color=config.colors.shares,
            va="top",
            backgroundcolor=config.colors.axis,
        )

    def label_graph_shares_b(ax):
        if config.anon:
            txtstr = f"Bought =\n{pcgr:2.0f}% of growth"
        else:
            val = sharebuy.iat[-1] - sharebuy.iat[0]
            txtstr = "Bought " + int_to_dollars(config, val) + f"\n{pcgr:2.0f}% of growth"
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        ax.text(
            x_min + 0.95 * (x_max - x_min),
            y_min + 0.05 * (y_max - y_min),
            txtstr,
            color=config.colors.expend,
            ha="right",
            backgroundcolor=config.colors.axis,
        )

    if config.anon:
        ax.set_yticklabels([])
        ax33.set_yticklabels([])

    if not config.expend_bool:
        label_graph_shares_a(ax)
        return 0

    sharesum = data_sp["TotalExpend"].cumsum()
    sharebuy = pd.Series(sharesum[config.win_sp_ind]).reset_index(drop=True)
    bought = sharebuy.iat[-1] - sharebuy.iat[0]
    profitloss = shares2.iat[-1] - sharebuy.iat[-1]
    pcgr = 100 * bought / gain

    ax33.plot(
        data_sp.Days[config.win_sp_ind], sharesum[config.win_sp_ind], **config.dotstyle, color=config.colors.expend
    )

    yticks1 = ax.get_yticks()
    dy = yticks1[1] - yticks1[0]
    yytickx = np.arange(yticks1[0], yticks1[-1] + dy, dy)
    ax.set_yticks(yytickx)
    ax.set_ylim(yytickx[0] - dy, yytickx[-1])
    # "-dy" to bump up this line one tick to avoid sometimes clashes with other line
    yylim1 = ax.get_ylim()

    yticks2 = ax33.get_yticks()
    ax33.set_ylim(yticks2[0], yticks2[-1])
    yytickx = np.arange(yticks2[0], yticks2[-1] + dy, dy)
    ax33.set_yticks(yytickx)
    ax33.set_ylim(yytickx[0], yytickx[-1])
    yylim2 = ax33.get_ylim()

    yrange = max(yylim1[1] - yylim1[0], yylim2[1] - yylim2[0])

    ax.set_ylim(yylim1[0], yylim1[0] + yrange)
    ax33.set_ylim(yylim2[0], yylim2[0] + yrange)

    yticks_dollars(config, ax)
    yticks_dollars(config, ax33)
    label_graph_shares_a(ax)
    label_graph_shares_b(ax)

    if config.anon:
        ax.set_yticklabels([])
        ax33.set_yticklabels([])

    return profitloss


def panel_super_window(config, ax, data):
    color_axes(config, ax)

    if not config.super_bool:
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        return None

    ax.plot(
        data.Days[config.window_ind],
        data["TotalSuper"][config.window_ind],
        config.marker,
        linestyle="-",
        color=config.colors.super,
        markersize=config.markersize,
    )

    for col in config.super_cols:
        ax.plot(
            data.Days[config.window_ind],
            data[col][config.window_ind],
            config.marker,
            linestyle="-",
            #            color=config.colors.cash,
            markersize=config.markersize,
        )

    yticks_dollars(config, ax)
    ax.set_xlabel(f"Years since {config.since_yr}", color=config.colors.label)
    ax.xaxis.set_minor_locator(AutoMinorLocator(3))
    ax.grid(which="major", color=config.colors.grid, linestyle="-", linewidth=0.5)
    ax.grid(which="minor", color=config.colors.grid, linestyle="-", linewidth=0.5)

    faux_title(config, ax, "Super")
    return None


############## PANEL 4: Total Window


def panel_income_breakdown(config, data, ax):
    color_axes(config, ax)

    if not config.iminor_bool:
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        return

    lbl_font = {"color": config.colors.text, "fontweight": "bold"}

    pc_font = {"color": config.colors.contrast, "fontsize": 10, "rotation": 90, "va": "bottom"}

    def sankey_income(data, income_cols):
        total_by_yr = {}
        for yr in config.years_uniq:
            total_by_yr[f"f{yr}"] = income_cols
            total_by_yr[yr] = get_inc_totals(data[data["Year"] == yr], income_cols).values()
        return pd.DataFrame(total_by_yr)

    ssdata = sankey_income(data, config.income_minor)
    sdata = ssdata.iloc[:, -2:]
    sdata = sdata.set_index(sdata.columns[0])
    ssort = sdata.to_dict(orient="dict")
    sd = ssort[next(iter(ssort))]
    sky.sankey(
        ax=ax,
        data=ssdata,
        titles=[yrlbl(i) for i in config.years_uniq],
        other_thresh=100,
        sort=config.sankey_sort,
        sort_dict=sd,
        node_gap=0.00,
        node_width=config.node_width,
        label_loc=["right", "left", "left"],
        label_font=lbl_font,
        label_path_effects=config.label_path_effects,
        label_dict=config.hdrnew,
        label_largest=True,
        value_loc=["center", "center", "center"],
        node_alpha=config.node_alpha,
        flow_alpha=config.flow_alpha,
        title_side="none",
        percent_loc="center",
        percent_loc_ht=0.05,
        percent_font=pc_font,
        percent_thresh=0.2,
        percent_thresh_ofmax=0.2,
        label_thresh_ofmax=0.2,
        label_values=not (config.anon),
        colormap=config.sankey_colormaps[1],
        value_fn=lambda x: "\n" + int_to_dollars(config, x),
    )

    ax.axis("on")

    yticks_dollars(config, ax)
    ax.yaxis.set_tick_params(which="both", direction="out", right=True, left=True)
    ax.set_ylim([0, ax.get_ylim()[1]])
    faux_title(config, ax, "'Other' income breakdown")
    if config.anon:
        ax.set_yticklabels([])


############## PANEL 5: Shares Breakdown


def panel_shares_breakdown(config, data, ax):
    color_axes(config, ax)

    if not config.shares_bool:
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        return

    lbl_font = {"color": config.colors.text, "fontweight": "bold"}

    pc_font = {"color": config.colors.contrast, "fontsize": 10, "rotation": 90, "va": "bottom"}

    def get_shares_totals(data, cols):
        total = {}
        for col in cols:
            total[col] = list(data[col])[-1]
        return total

    def sankey_shares_makeup(data):
        total_by_yr = {}
        for yr in config.years_uniq:
            total_by_yr[f"f{yr}"] = config.shares_cols
            total_by_yr[yr] = get_shares_totals(data[data["Year"] == yr], config.shares_cols).values()
        return pd.DataFrame(total_by_yr)

    sky.sankey(
        ax=ax,
        data=sankey_shares_makeup(data),
        titles=[yrlbl(i) for i in config.years_uniq],
        colormap=config.sankey_colormaps[2],
        sort=config.sankey_sort,
        node_gap=0.00,
        label_dict=config.hdrnew,
        label_values=not (config.anon),
        label_thresh_ofmax=0.10,
        node_width=config.node_width,
        label_loc=["right", "left", "left"],
        label_largest=True,
        label_font=lbl_font,
        label_path_effects=config.label_path_effects,
        value_loc=["none", "none", "none"],
        value_fn=lambda x: "\n" + int_to_dollars(config, x),
        node_alpha=config.node_alpha,
        flow_alpha=config.flow_alpha,
        title_side="none",
        percent_loc="center",
        percent_loc_ht=0.05,
        percent_font=pc_font,
        percent_thresh=0.1,
        percent_thresh_ofmax=0.2,
    )

    ax.axis("on")
    ax.set_ylim([0, ax.get_ylim()[1]])
    ax.set_yticks(ax.get_yticks())
    ax.yaxis.tick_right()

    yticks_dollars(config, ax)
    ax.yaxis.set_tick_params(which="both", direction="out", right=True, left=True)

    faux_title(config, ax, "Shares breakdown")

    if config.anon:
        ax.set_yticklabels([])


def panel_super_breakdown(config, data, ax):
    color_axes(config, ax)

    if not config.super_bool:
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        return

    lbl_font = {"color": config.colors.text, "fontweight": "bold"}

    pc_font = {"color": config.colors.contrast, "fontsize": 10, "rotation": 90, "va": "bottom"}

    def get_super_totals(data, cols):
        total = {}
        for col in cols:
            total[col] = list(data[col])[-1]
        return total

    def sankey_super_makeup(data):
        total_by_yr = {}
        for yr in config.years_uniq:
            total_by_yr[f"f{yr}"] = config.super_cols
            total_by_yr[yr] = get_super_totals(data[data["Year"] == yr], config.super_cols).values()
        return pd.DataFrame(total_by_yr)

    sky.sankey(
        ax=ax,
        data=sankey_super_makeup(data),
        titles=[yrlbl(i) for i in config.years_uniq],
        colormap=config.sankey_colormaps[2],
        sort=config.sankey_sort,
        node_gap=0.00,
        label_dict=config.hdrnew,
        label_values=not (config.anon),
        label_thresh_ofmax=0.10,
        node_width=config.node_width,
        label_loc=["right", "left", "left"],
        label_largest=True,
        label_font=lbl_font,
        label_path_effects=config.label_path_effects,
        value_loc=["none", "none", "none"],
        value_fn=lambda x: "\n" + int_to_dollars(config, x),
        node_alpha=config.node_alpha,
        flow_alpha=config.flow_alpha,
        title_side="none",
        percent_loc="center",
        percent_loc_ht=0.05,
        percent_font=pc_font,
        percent_thresh=0.1,
        percent_thresh_ofmax=0.2,
    )

    ax.axis("on")
    ax.set_ylim([0, ax.get_ylim()[1]])
    ax.set_yticks(ax.get_yticks())
    ax.yaxis.tick_right()

    yticks_dollars(config, ax)
    ax.yaxis.set_tick_params(which="both", direction="out", right=True, left=True)

    faux_title(config, ax, "Super breakdown")

    if config.anon:
        ax.set_yticklabels([])


def panel_cash_breakdown(config, data, ax):
    color_axes(config, ax)

    if not config.cash_bool:
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        return

    lbl_font = {"color": config.colors.text, "fontweight": "bold"}

    pc_font = {"color": config.colors.contrast, "fontsize": 10, "rotation": 90, "va": "bottom"}

    def get_cash_totals(data, cols):
        total = {}
        for col in cols:
            total[col] = list(data[col])[-1]
        return total

    def sankey_cash_makeup(data):
        total_by_yr = {}
        for yr in config.years_uniq:
            total_by_yr[f"f{yr}"] = config.cash_cols
            total_by_yr[yr] = get_cash_totals(data[data["Year"] == yr], config.cash_cols).values()
        return pd.DataFrame(total_by_yr)

    sky.sankey(
        ax=ax,
        data=sankey_cash_makeup(data),
        titles=[yrlbl(i) for i in config.years_uniq],
        colormap=config.sankey_colormaps[2],
        sort=config.sankey_sort,
        node_gap=0.00,
        label_dict=config.hdrnew,
        label_values=not (config.anon),
        label_thresh_ofmax=0.10,
        node_width=config.node_width,
        label_loc=["none", "none", "left"],
        label_font=lbl_font,
        label_path_effects=config.label_path_effects,
        value_loc=["none", "none", "none"],
        value_fn=lambda x: "\n" + int_to_dollars(config, x),
        node_alpha=config.node_alpha,
        flow_alpha=config.flow_alpha,
        title_side="none",
        percent_loc="center",
        percent_loc_ht=0.05,
        percent_font=pc_font,
        percent_thresh=0.1,
        percent_thresh_ofmax=0.2,
    )

    ax.axis("on")
    ax.set_ylim([0, ax.get_ylim()[1]])
    ax.set_yticks(ax.get_yticks())
    ax.yaxis.tick_right()

    yticks_dollars(config, ax)
    ax.yaxis.set_tick_params(which="both", direction="out", right=True, left=True)

    faux_title(config, ax, "Cash breakdown")

    if config.anon:
        ax.set_yticklabels([])


def panel_income(config, ax4, alldata):
    color_axes(config, ax4)

    if not config.income_bool:
        ax4.set_xticklabels([])
        ax4.set_yticklabels([])
        return

    lbl_font = {"color": config.colors.text, "fontweight": "bold"}

    pc_font = {"color": config.colors.contrast, "fontsize": 10, "rotation": 90, "va": "bottom"}

    sky.sankey(
        ax=ax4,
        data=sankey_income(config, alldata, config.income_cols),
        titles=[yrlbl(i) for i in config.years_uniq],
        other_thresh_ofsum=config.income_thresh,
        sort=config.sankey_sort,
        node_gap=0.00,
        node_width=config.node_width,
        label_largest=True,
        label_loc=["right", "left", "left"],
        label_font=lbl_font,
        label_path_effects=config.label_path_effects,
        label_dict=config.hdrnew,
        label_thresh_ofmax=0.2,
        value_loc=["none", "none", "none"],
        node_alpha=config.node_alpha,
        flow_alpha=config.flow_alpha,
        title_side="none",
        percent_loc="center",
        percent_loc_ht=0.05,
        percent_font=pc_font,
        percent_thresh=0.2,
        percent_thresh_ofmax=0.2,
        colormap=config.sankey_colormaps[0],
        label_values=not (config.anon),
        value_fn=lambda x: "\n" + int_to_dollars(config, x),
    )

    ax4.axis("on")
    ax4.set_xticklabels(())
    # ax4.set_xticklabels([i for i in ax4.get_xticklabels()],rotation=90,color=config.colors.tick)
    ax4.yaxis.set_tick_params(which="both", direction="out", right=True, left=True)
    ax4.set_ylim(0, ax4.get_ylim()[1])
    yticks_dollars(config, ax4)

    if config.anon:
        ax4.set_yticklabels([])


################################


def panel_shares(config, ax, alldata):
    color_axes(config, ax)

    if not config.shares_bool:
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        return

    lbl_font = {"color": config.colors.text, "fontweight": "bold"}
    pc_font = {"color": config.colors.contrast, "fontsize": 10, "rotation": 90, "va": "bottom"}

    cdict = {
        "Bought": config.colors.expend,
        "Growth": config.colors.shares,
    }
    sky.sankey(
        ax=ax,
        data=sankey_shares(config, alldata),
        titles=[yrlbl(i) for i in config.years_uniq],
        colormap="Pastel2",
        sort=config.sankey_sort,
        node_gap=0.00,
        color_dict=cdict,
        node_width=config.node_width,
        label_loc=["right", "left", "left"],
        label_largest=True,
        label_font=lbl_font,
        label_path_effects=config.label_path_effects,
        value_loc=["none", "none", "none"],
        node_alpha=config.node_alpha,
        flow_alpha=config.flow_alpha,
        title_side="none",
        percent_loc="center",
        percent_loc_ht=0.05,
        percent_font=pc_font,
        percent_thresh=0.2,
        percent_thresh_ofmax=0.2,
        label_values=not (config.anon),
        label_thresh_ofmax=0.2,
        value_fn=lambda x: "\n" + int_to_dollars(config, x),
    )

    ax.axis("on")
    ax.set_xticklabels(())
    ax.yaxis.tick_right()
    # ax5.set_xticklabels([i for i in ax5.get_xticklabels()],rotation=90,color=config.colors.tick)
    ax.yaxis.set_tick_params(which="both", direction="out", right=True, left=True)
    ax.set_ylim(0, ax.get_ylim()[1])
    yticks_dollars(config, ax)
    if config.anon:
        ax.set_yticklabels([])


################################


def color_axes(config, ax):
    ax.set_facecolor(config.colors.axis)
    for sp in ax.spines:
        ax.spines[sp].set_color(config.colors.frame)
    ax.tick_params(axis="x", colors=config.colors.frame)
    ax.tick_params(axis="y", colors=config.colors.frame)
    ax.tick_params(labelcolor=config.colors.tick)


def yrlbl(yr):
    yrstr = f"{yr}"
    return "'" + yrstr[2:4]


def yticks_dollars(config, ax):
    ticks = ax.get_yticks()
    ax.set_yticks(ticks)
    newticks = [int_to_dollars(config, int(tick)) for tick in ticks]
    ax.set_yticklabels(newticks)


def int_to_dollars(config, xx, plussig=0):
    x = abs(round(xx))
    sgn = "-" if xx < 0 else ""
    amt_k = 1_000
    amt_m = 1_000_000
    amt_b = 1_000_000_000
    if x < amt_k:
        div = 1
        suffix = ""
        sig = 0
    elif x >= amt_k and x < 10 * amt_k:
        div = amt_k
        suffix = "k"
        sig = 1
    elif x >= 10 * amt_k and x < amt_m:
        div = amt_k
        suffix = "k"
        sig = 0
    elif x >= amt_m and x < 10 * amt_m:
        div = amt_m
        suffix = "M"
        sig = 2
    elif x >= 10 * amt_m and x < amt_b:
        div = amt_m
        suffix = "M"
        sig = 1
    elif x >= amt_b and x < 10 * amt_b:
        div = amt_b
        suffix = "B"
        sig = 2
    else:
        div = amt_b
        suffix = "B"
        sig = 1
    return sgn + config.currencysign + f"{ x / div :.{sig+plussig}f}" + suffix


def yticks_equalise(config, ax4, ax5):
    ymax = max(ax4.get_ylim()[1], ax5.get_ylim()[1])
    ax4.set_ylim([0, ymax])
    ax5.set_ylim([0, ymax])
    ax4.set_yticks(ax4.get_yticks())
    ax5.set_yticks(list(ax4.get_yticks()))
    yticks_dollars(config, ax4)
    yticks_dollars(config, ax5)


def faux_title(config, ax, txtstr):
    xrange = np.diff(ax.get_xlim())
    ax.text(
        ax.get_xlim()[0] + 0.04 * xrange,
        0.95 * ax.get_ylim()[1],
        txtstr,
        color=config.colors.title,
        ha="left",
        va="top",
        backgroundcolor=config.colors.axis,
    )


############## SANKEY SETUP


def get_totals(data, val, spend):
    shares = data[data[val] > 0]
    total = {}
    total["Bought"] = sum(data[spend])
    total["Growth"] = max(shares[val]) - min(shares[val]) - sum(data[spend])
    return total


def sankey_shares(config, data):
    total_by_yr = {}
    for yr in config.years_uniq:
        total_by_yr[f"f{yr}"] = ["Bought", "Growth"]
        total_by_yr[yr] = get_totals(data[data["Year"] == yr], "TotalShares", "TotalExpend").values()
    return pd.DataFrame(total_by_yr)


def sankey_income(config, data, income_cols):
    total_by_yr = {}
    for yr in config.years_uniq:
        total_by_yr[f"f{yr}"] = income_cols
        total_by_yr[yr] = get_inc_totals(data[data["Year"] == yr], income_cols).values()
    return pd.DataFrame(total_by_yr)


def get_inc_totals(data, income_cols):
    total = {}
    for col in income_cols:
        total[col] = sum(data[col])
    return total


################################

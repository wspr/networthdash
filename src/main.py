import os
from datetime import datetime, timezone

import ausankey as sky
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import AutoMinorLocator

from networthdash.src.config import Config

############# PARAM ##############


def dashboard(config: Config):
    # internal parameters
    # (possibly to generalise later)

    expstart = 0

    main_wd = 0.75
    main_ht = 0.30
    inset_w = 0.35
    inset_h = 0.15
    sankey_w = 0.375
    sankey_h = 0.15

    inset_x = [0.1, 0.55]
    row_y = [0.05, 0.44, 0.79]
    row_gap = 0.03

    # process Config parameters

    retire_yr = config.born_yr + config.retire_age
    ahead_yr = datetime.now(timezone.utc).year + config.future_window
    max_yr = min(ahead_yr, retire_yr)

    winyr = config.linear_window
    anon = config.anon

    saveprefix = config.saveprefix or os.path.splitext(config.csv)[0]

    datecol = "Date" #config.strings.datecol

    ############# HELPERS

    errors = {}
    errors["DateColMissing"] = f"One column must be called '{datecol}'."
    
    def color_axes(ax):
        ax.set_facecolor(config.colors.axis)
        for sp in ax.spines:
            ax.spines[sp].set_color(config.colors.frame)
        ax.tick_params(axis="x", colors=config.colors.frame)
        ax.tick_params(axis="y", colors=config.colors.frame)
        ax.tick_params(labelcolor=config.colors.tick)

    def dates_to_years(alldata):
        allcols = alldata.columns.tolist()
        if not datecol in allcols:
            raise RuntimeError(errors.DateColMissing)
    
        return alldata[datecol].apply(lambda x: 
            datetime.strptime(x, config.datefmt).replace(tzinfo=timezone.utc).year )

    def dates_to_days(data,sincedate):
        days = np.empty(len(data[datecol]))
        for ii,ent in enumerate(data[datecol]):
            y = datetime.strptime(ent, config.datefmt).replace(tzinfo=timezone.utc)
            days[ii] = (y - sincedate).days / 365
        return days

    def int_to_dollars(x, plussig=0):
        x = round(x)
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
        return config.currencysign + f"{ x / div :.{sig+plussig}f}" + suffix

    def yticks_dollars(ax):
        ticks = ax.get_yticks()
        ax.set_yticks(ticks)
        newticks = [int_to_dollars(int(tick)) for tick in ticks]
        ax.set_yticklabels(newticks)

    dotstyle = {
        "marker": config.marker,
        "markersize": config.markersize,
        "linestyle": "None",
    }

    projstyle = {
        "linestyle": "-",
        "marker": "None",
        "linewidth": config.linewidth / 4,
    }

    ############# HEADERS

    hdr = pd.read_csv(config.csvpath + config.csv, na_values=0, header=None, nrows=2).transpose()

    hdrnew = {}
    for ii,_ in enumerate(hdr[1]):
        prefix = hdr[0][ii] if isinstance(hdr[0][ii],str) else "_"
        tmpstr = datecol if hdr[1][ii] == datecol else prefix + "_" + hdr[1][ii]
        hdrnew[tmpstr] = hdr[1][ii]

    hdr[1] = list(hdrnew.keys())
    super_cols = list(hdr[1][hdr[0] == "Super"])
    shares_cols = list(hdr[1][hdr[0] == "Shares"])
    cash_cols = list(hdr[1][hdr[0] == "Cash"])
    expend_cols = list(hdr[1][hdr[0] == "Expend"])
    income_cols = list(hdr[1][hdr[0] == "Income"])

    ############# DATA

    alldata = pd.read_csv(config.csvpath + config.csv, na_values=0, header=1)
    alldata = alldata.fillna(0)
    alldata.columns = hdr[1]
    alldata["Year"] = dates_to_years(alldata)

    since_yr = config.since_yr or min(alldata.Year)
    until_yr = config.until_yr or max(alldata.Year)
    sincedate = datetime(since_yr, 1, 1, tzinfo=timezone.utc)
    years_until_retire = max_yr - since_yr
    age_at_retirement = max_yr - config.born_yr

    alldata["Days"] = dates_to_days(alldata, sincedate)
    alldata = alldata.sort_values(by="Days")
    alldata = alldata.reset_index(drop=True)

    alldata["TotalSuper"] = alldata[super_cols].sum(axis=1)
    alldata["TotalShares"] = alldata[shares_cols].sum(axis=1)
    alldata["TotalCash"] = alldata[cash_cols].sum(axis=1)
    expend = alldata[expend_cols].sum(axis=1)
    income = alldata[income_cols].sum(axis=1)

    alldata["TotalExpend"] = expend
    alldata["TotalIncome"] = income
    alldata["Total"] = alldata["TotalShares"] + alldata["TotalSuper"] + alldata["TotalCash"]

    income_grand_tot = alldata["TotalIncome"].sum()
    income_sum = alldata[income_cols].sum()
    income_minor = list(income_sum[income_sum < (1 - config.income_thresh) * income_grand_tot].keys())

    years_uniq = {}
    for x in alldata["Year"]:
        if x >= since_yr and x <= until_yr:
            years_uniq[x] = True

    data = alldata[alldata.Total > 0]
    data = data.reset_index(drop=True)

    data_sp = alldata[alldata.TotalExpend > 0]
    data_sp = data_sp.reset_index(drop=True)

    window_ind = data.Days > (data.Days.iat[-1] - winyr)
    win_sp_ind = data_sp.Days > (data_sp.Days.iat[-1] - winyr)

    data["TotalSuper"] = data[super_cols].sum(axis=1)
    data["TotalShares"] = data[shares_cols].sum(axis=1)
    data["TotalCash"] = data[cash_cols].sum(axis=1)
    data["Total"] = data["TotalShares"] + data["TotalSuper"] + data["TotalCash"]

    ########### CREATE FIGURE and AXES

    fig, ax0 = plt.subplots(
        figsize=(config.figw, config.figh),
        facecolor=config.colors.bg,
    )
    ax0.axis("off")

    ax1 = fig.add_axes([(1 - main_wd) / 2, row_y[1], main_wd, main_ht])
    ax = ax1
    ax2 = fig.add_axes([inset_x[0], row_y[2], inset_w, inset_h])
    ax3 = fig.add_axes([inset_x[1], row_y[2], inset_w, inset_h])
    ax6 = fig.add_axes([inset_x[0], row_y[0], sankey_w, sankey_h])
    ax7 = fig.add_axes([inset_x[1] - 0.02, row_y[0], sankey_w, sankey_h])
    # ax4 = fig.add_axes([0.1, row_y[0], 0.4, 0.2])
    # ax5 = fig.add_axes([0.5, row_y[0], 0.4, 0.2])
    ax4 = fig.add_axes([inset_x[0], row_gap + row_y[0] + sankey_h, sankey_w, sankey_h])
    ax5 = fig.add_axes([inset_x[1] - 0.02, row_gap + row_y[0] + sankey_h, sankey_w, sankey_h])

    color_axes(ax1)
    color_axes(ax2)
    color_axes(ax3)
    color_axes(ax4)
    color_axes(ax5)
    color_axes(ax6)
    color_axes(ax7)

    ########### FITTING and PLOTTING

    ax1.set_title("", color=config.colors.title)
    ax1.axvline(x=data.Days.iat[-1], linestyle="--", color=config.colors.dashes)

    if retire_yr == max_yr:
        ax1.axvline(x=retire_yr - since_yr, linestyle="--", color=config.colors.dashes)

    def extrap(d, t):
        reg = np.polyfit(d, t, 1)
        rd = np.linspace(data.Days[window_ind].iat[0], years_until_retire)
        yd = rd * reg[0] + reg[1]
        return rd, yd

    def extrap_exp(ax, d, t, arg):
        clim = ax.get_ylim()
        logfit = np.polyfit(d, np.log(t), 1, w=np.sqrt(t))
        rd = np.linspace(d.iloc[0], years_until_retire)
        yd = np.exp(logfit[1]) * np.exp(logfit[0] * rd)
        infl = np.exp(logfit[0]) - 1
        hp = ax.plot(rd, yd, **(projstyle | arg))
        ax.set_ylim(clim)
        return hp, infl

    rd1, yd1 = extrap(data.Days[window_ind], data.Total[window_ind])
    rd2, yd2 = extrap(data.Days[window_ind], data.TotalSuper[window_ind])
    rd3, yd3 = extrap(data.Days[window_ind], data.TotalShares[window_ind])
    retire_worth = yd1[-1]

    hp1 = ax.plot(rd1, yd1, **projstyle, color=config.colors.total)
    hp2 = ax.plot(rd2, yd2, **projstyle, color=config.colors.super)
    hp3 = ax.plot(rd3, yd3, **projstyle, color=config.colors.shares)

    hp11, tot_growth = extrap_exp(ax, data.Days[expstart:-1], data.Total[expstart:-1], get_col(hp1[0]))

    ind = data.TotalSuper[expstart:-1] > 0
    days = data.Days[expstart:-1][ind]
    val = data.TotalSuper[expstart:-1][ind]
    extrap_exp(ax, days, val, get_col(hp2[0]))

    ind = data["TotalShares"][expstart:-1] > 0
    days = data.Days[expstart:-1][ind]
    val = data["TotalShares"][expstart:-1][ind]
    extrap_exp(ax, days, val, get_col(hp3[0]))
    ax.plot(data.Days, data.Total, **get_col(hp1[0]), **dotstyle)
    ax.plot(data.Days, data["TotalShares"], color=hp3[0].get_color(), **dotstyle)
    ax.plot(data.Days, data.TotalSuper, **get_col(hp2[0]), **dotstyle)
    hp4 = ax.plot(data.Days, data["TotalCash"], **dotstyle, color=config.colors.cash)

    ############% LABELS

    va = "center"
    ax.text(data.Days.iat[-1], alldata["TotalCash"].iat[-1], "  Cash", color=hp4[0].get_color(), va=va)
    ax.text(data.Days.iat[-1], alldata["TotalShares"].iat[-1], "  Shares", color=hp3[0].get_color(), va=va)
    ax.text(data.Days.iat[-1], alldata["TotalSuper"].iat[-1], "  Super", color=hp2[0].get_color(), va=va)

    txtstr = "  Total" if anon else ("  Total\n  " + int_to_dollars(data.Total.iat[-1]))

    ax.text(data.Days.iat[-1], data.Total.iat[-1], txtstr, va="center", color=hp1[0].get_color())

    ax.set_xticks(range(years_until_retire + 1))
    ax.set_xticklabels(range(since_yr, since_yr + years_until_retire + 1), rotation=90, color=config.colors.tick)
    clim = ax.get_ylim()
    ax.set_ylim(0, clim[1])
    yticks_dollars(ax1)
    ax.set_ylim(0, clim[1])

    if not anon:
        txtstr = (
            f"Exp growth rate:\n{tot_growth*100:2.1f}% p.a."
            f"\n\nNet worth\nat age {age_at_retirement}\n= "
            f"{int_to_dollars(retire_worth)}"
            f"\n\n{config.retire_ratio:.1%} rule\n= "
            f"{int_to_dollars(config.retire_ratio*retire_worth)}"
            f"/yr"
        )
        ax.text(
            data.Days[0],
            0.95 * clim[1],
            txtstr,
            ha="left",
            va="top",
            color=config.colors.text,
        )

    #######%%###### EXTRAP

    def extrap_target(yy):
        if data.Total.iat[-1] > 0.8 * yy:
            return

        reg = np.polyfit(data.Days[window_ind], data.Total[window_ind], 1)

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
            int_to_dollars(yy),
            ha="center",
            va="bottom",
            color=config.colors.text,
        )

    if not anon:
        for ii in config.linear_targets:
            if ii < 0.85 * ax.get_ylim()[1]:
                extrap_target(ii)

    ############## INSET
    
    reg = np.polyfit(data.Days[window_ind],data.Total[window_ind],1)
    rd = np.linspace(data.Days[window_ind].iat[0],data.Days.iat[-1])
    yd = rd*reg[0] + reg[1]
    ax2.plot(rd,yd,"-",lw=config.linewidth/4,color=hp1[0].get_color())
    ax2.plot(
        data.Days[window_ind],data.Total[window_ind],
        **get_col(hp1[0]),**dotstyle)
    
    logfit = np.polyfit(data.Days[window_ind],np.log(data.Total[window_ind]),1,w=np.sqrt(data.Total[window_ind]))
    rd = np.linspace(data.Days[window_ind].iat[0],data.Days.iat[-1])
    yd = np.exp(logfit[1])*np.exp(logfit[0]*rd)
    ax2.plot(rd,yd,"--",lw=config.linewidth/4,color=hp11[0].get_color())
    
    ax2.set_xlabel(f"Years since {since_yr}",color=config.colors.label)
    yticks_dollars(ax2)

    ax2.xaxis.set_minor_locator(AutoMinorLocator(3))
    ax2.grid(which="major", color=config.colors.grid, linestyle="-", linewidth=0.5)
    ax2.grid(which="minor", color=config.colors.grid, linestyle="-", linewidth=0.5)

    gain = data.Total[window_ind].iat[-1] - data.Total[window_ind].iat[0]
    elap = data.Days[window_ind].iat[-1] - data.Days[window_ind].iat[0]

    ax2.tick_params(axis="y", labelcolor=hp1[0].get_color())

    x_min, x_max = ax2.get_xlim()
    y_min, y_max = ax2.get_ylim()

    if anon:
        ax2.text(
            x_min + 0.05 * (x_max - x_min),
            y_min + 0.95 * (y_max - y_min),
            "Net worth\nincrease",
            color=hp1[0].get_color(),
            va="top",
        )
    else:
        peryrtext = "" if winyr == 1 else ("\n" + int_to_dollars(gain / elap) + "/yr")
        txtstr = "Net worth\nincrease\n" + int_to_dollars(gain) + peryrtext
        ax2.text(
            x_min + 0.05 * (x_max - x_min),
            y_min + 0.95 * (y_max - y_min),
            txtstr,
            color=hp1[0].get_color(),
            va="top",
            backgroundcolor=config.colors.axis,
        )

    ############## INSET 2

    ax3.plot(
        data.Days[window_ind],
        data["TotalShares"][window_ind],
        config.marker,
        color=hp3[0].get_color(),
        markersize=config.markersize,
    )
    ax3.set_xlabel(f"Years since {since_yr}", color=config.colors.label)

    ax33 = ax3.twinx()
    color_axes(ax33)

    sharesum = data_sp["TotalExpend"].cumsum()
    hp7 = ax33.plot(data_sp.Days[win_sp_ind], sharesum[win_sp_ind], **dotstyle, color=config.colors.expend)

    yticks1 = ax3.get_yticks()
    yticks2 = ax33.get_yticks()

    dy = yticks1[1] - yticks1[0]
    ax3.set_ylim(
        yticks1[0] - dy, yticks1[-1]
    )  # "-dy" to bump up this line one tick to avoid sometimes clashes with other line
    ax33.set_ylim(yticks2[0], yticks2[-1])

    yylim1 = ax3.get_ylim()
    yylim2 = ax33.get_ylim()

    yrange = max(yylim1[1] - yylim1[0], yylim2[1] - yylim2[0])

    ax3.set_ylim(yylim1[0], yylim1[0] + yrange)
    ax33.set_ylim(yylim2[0], yylim2[0] + yrange)

    yticks1 = ax3.get_yticks()
    yticks2 = ax33.get_yticks()

    yticks_dollars(ax3)
    yticks_dollars(ax33)

    ax3.set_ylim(yylim1[0], yylim1[0] + yrange)
    ax33.set_ylim(yylim2[0], yylim2[0] + yrange)
    ax3.tick_params(axis="y", labelcolor=hp3[0].get_color())
    ax33.tick_params(axis="y", labelcolor=hp7[0].get_color())

    ax3.xaxis.set_minor_locator(AutoMinorLocator(3))
    ax3.grid(which="major", color=config.colors.grid, linestyle="-", linewidth=0.5)
    ax3.grid(which="minor", color=config.colors.grid, linestyle="-", linewidth=0.5)

    shares2 = pd.Series(data["TotalShares"][window_ind]).reset_index(drop=True)
    sharebuy = pd.Series(sharesum[win_sp_ind]).reset_index(drop=True)
    pcgr = 100 * (sharebuy.iat[-1] - sharebuy.iat[1]) / (shares2.iat[-1] - shares2.iat[1])

    profitloss = shares2.iat[-1] - sharebuy.iat[-1]
    gain = shares2.iat[-1] - shares2.iat[1]
    elap = data.Days[window_ind].iat[-1] - data.Days[window_ind].iat[0]

    x_min, x_max = ax3.get_xlim()
    y_min, y_max = ax3.get_ylim()
    if anon:
        ax3.text(
            x_min + 0.05 * (x_max - x_min),
            y_min + 0.95 * (y_max - y_min),
            "Shares\nincrease",
            color=hp3[0].get_color(),
            va="top",
            backgroundcolor=config.colors.axis,
        )
    else:
        peryrtext = "" if winyr == 1 else ("\n" + int_to_dollars(gain / elap) + "/yr")
        ax3.text(
            x_min + 0.05 * (x_max - x_min),
            y_min + 0.95 * (y_max - y_min),
            "Shares\nincrease\n" + int_to_dollars(gain) + peryrtext,
            color=hp3[0].get_color(),
            va="top",
            backgroundcolor=config.colors.axis,
        )

    if anon:
        ax3.text(
            x_min + 0.95 * (x_max - x_min),
            y_min + 0.05 * (y_max - y_min),
            f"Bought =\n{pcgr:2.0f}% of growth",
            color=hp7[0].get_color(),
            ha="right",
            backgroundcolor=config.colors.axis,
        )
    else:
        val = sharebuy.iat[-1] - sharebuy.iat[1]
        txtstr = "Bought " + int_to_dollars(val) + f"\n{pcgr:2.0f}% of growth"
        ax3.text(
            x_min + 0.95 * (x_max - x_min),
            y_min + 0.05 * (y_max - y_min),
            txtstr,
            color=hp7[0].get_color(),
            ha="right",
            backgroundcolor=config.colors.axis,
        )

    ############## SANKEY SETUP

    def get_inc_totals(data, income_cols):
        total = {}
        for col in income_cols:
            total[col] = sum(data[col])
        return total

    def get_shares_totals(data, cols):
        total = {}
        for col in cols:
            total[col] = list(data[col])[-1]
        return total

    def sankey_income(data, income_cols):
        total_by_yr = {}
        for yr in years_uniq:
            total_by_yr[f"f{yr}"] = income_cols
            total_by_yr[yr] = get_inc_totals(data[data["Year"] == yr], income_cols).values()
        return pd.DataFrame(total_by_yr)

    def get_totals(data, val, spend):
        shares = data[data[val] > 0]
        total = {}
        total["Bought"] = sum(data[spend])
        total["Growth"] = max(shares[val]) - min(shares[val]) - sum(data[spend])
        return total

    def sankey_shares(data):
        total_by_yr = {}
        for yr in years_uniq:
            total_by_yr[f"f{yr}"] = ["Bought", "Growth"]
            total_by_yr[yr] = get_totals(data[data["Year"] == yr], "TotalShares", "TotalExpend").values()
        return pd.DataFrame(total_by_yr)

    def sankey_shares_makeup(data):
        total_by_yr = {}
        for yr in years_uniq:
            total_by_yr[f"f{yr}"] = shares_cols
            total_by_yr[yr] = get_shares_totals(data[data["Year"] == yr], shares_cols).values()
        return pd.DataFrame(total_by_yr)

    ############## SANKEY

    def yrlbl(yr):
        yrstr = f"{yr}"
        return "'" + yrstr[2:4]

    pc_font = {"color": config.colors.contrast, "fontsize": 10, "rotation": 90, "va": "bottom"}

    sky.sankey(
        ax=ax4,
        data=sankey_income(alldata, income_cols),
        titles=[yrlbl(i) for i in years_uniq],
        other_thresh_ofsum=config.income_thresh,
        sort="bottom",
        node_gap=0.00,
        node_width=config.node_width,
        label_loc=["none", "none", "left"],
        label_font={"color": config.colors.text},
        label_dict=hdrnew,
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
        label_values=not (anon),
        value_fn=lambda x: "\n" + int_to_dollars(x),
    )

    ssdata = sankey_income(alldata, income_minor)
    sdata = ssdata.iloc[:, -2:]
    sdata = sdata.set_index(sdata.columns[0])
    ssort = sdata.to_dict(orient="dict")
    sd = ssort[next(iter(ssort))]
    sky.sankey(
        ax=ax6,
        data=ssdata,
        titles=[yrlbl(i) for i in years_uniq],
        other_thresh=100,
        sort="bottom",
        sort_dict=sd,
        node_gap=0.00,
        node_width=config.node_width,
        label_loc=["none", "none", "left"],
        label_font={"color": config.colors.text},
        label_dict=hdrnew,
        value_loc=["center", "center", "center"],
        node_alpha=config.node_alpha,
        flow_alpha=config.flow_alpha,
        title_side="none",
        percent_loc=("none", "none", "center"),
        percent_loc_ht=0.05,
        percent_font=pc_font,
        percent_thresh=0.2,
        percent_thresh_ofmax=0.2,
        label_thresh_ofmax=0.2,
        label_values=not (anon),
        colormap=config.sankey_colormaps[1],
        value_fn=lambda x: "\n" + int_to_dollars(x),
    )

    sky.sankey(
        ax=ax5,
        data=sankey_shares(alldata),
        titles=[yrlbl(i) for i in years_uniq],
        colormap="Pastel2",
        sort="bottom",
        node_gap=0.00,
        color_dict={"Bought": config.colors.expend, "Growth": config.colors.shares},
        node_width=config.node_width,
        label_loc=["none", "none", "left"],
        label_font={"color": config.colors.text},
        value_loc=["none", "none", "none"],
        node_alpha=config.node_alpha,
        flow_alpha=config.flow_alpha,
        title_side="none",
        percent_loc="center",
        percent_loc_ht=0.05,
        percent_font=pc_font,
        percent_thresh=0.2,
        percent_thresh_val=20000,
        label_values=not (anon),
        label_thresh_ofmax=0.2,
        value_fn=lambda x: "\n" + int_to_dollars(x),
    )

    sky.sankey(
        ax=ax7,
        data=sankey_shares_makeup(alldata),
        titles=[yrlbl(i) for i in years_uniq],
        colormap=config.sankey_colormaps[2],
        sort="bottom",
        node_gap=0.00,
        label_dict=hdrnew,
        label_values=not (anon),
        label_thresh_ofmax=0.10,
        node_width=config.node_width,
        label_loc=["none", "none", "left"],
        label_font={"color": config.colors.text},
        value_loc=["none", "none", "none"],
        value_fn=lambda x: "\n" + int_to_dollars(x),
        node_alpha=config.node_alpha,
        flow_alpha=config.flow_alpha,
        title_side="none",
        percent_loc="center",
        percent_loc_ht=0.05,
        percent_font=pc_font,
        percent_thresh=0.1,
        percent_thresh_ofmax=0.2,
    )

    def faux_title(ax, txtstr):
        xrange = np.diff(ax.get_xlim())
        ax.text(
            ax.get_xlim()[0] + 0.02 * xrange,
            0.95 * ax.get_ylim()[1],
            txtstr,
            color=config.colors.title,
            ha="left",
            va="top",
        )

    ax4.axis("on")
    ax5.axis("on")
    ax6.axis("on")
    ax7.axis("on")

    ymax = max(ax4.get_ylim()[1], ax5.get_ylim()[1])
    ax4.set_ylim([0, ymax])
    ax5.set_ylim([0, ymax])
    ax6.set_ylim([0, ax6.get_ylim()[1]])
    ax7.set_ylim([0, ax7.get_ylim()[1]])

    ax4.set_yticks(ax4.get_yticks())
    ax6.set_yticks(ax6.get_yticks())
    ax7.set_yticks(ax7.get_yticks())

    ax5.set_yticks(list(ax4.get_yticks()))

    ax4.set_xticklabels(())
    ax5.set_xticklabels(())
    ax5.yaxis.tick_right()
    ax7.yaxis.tick_right()

    yticks_dollars(ax4)
    yticks_dollars(ax5)
    yticks_dollars(ax6)
    yticks_dollars(ax7)

    # ax4.set_xticklabels([i for i in ax4.get_xticklabels()],rotation=90,color=config.colors.tick)
    # ax5.set_xticklabels([i for i in ax5.get_xticklabels()],rotation=90,color=config.colors.tick)

    ax4.yaxis.set_tick_params(which="both", direction="out", right=True, left=True)
    ax5.yaxis.set_tick_params(which="both", direction="out", right=True, left=True)
    ax7.yaxis.set_tick_params(which="both", direction="out", right=True, left=True)

    faux_title(ax4, "Annual income")
    if anon:
        faux_title(ax5, "Annual shares increase")
    else:
        faux_title(ax5, "Annual shares increase\nAll-time profit = " + int_to_dollars(profitloss))
    faux_title(ax6, "'Other' income breakdown")
    faux_title(ax7, "Shares breakdown")

    ############## FINISH UP

    if anon:
        ax.set_yticklabels([])
        ax2.set_yticklabels([])
        ax3.set_yticklabels([])
        ax33.set_yticklabels([])
        ax4.set_yticklabels([])
        ax5.set_yticklabels([])
        ax6.set_yticklabels([])
        ax7.set_yticklabels([])
        ax.set_ylabel("Amount", color=config.colors.text)
        ax2.set_ylabel("Amount", color=config.colors.text)
        ax3.set_ylabel("Amount", color=config.colors.text)

    plt.show()

    filename = config.savedir + saveprefix + "-" + datetime.now(timezone.utc).strftime(config.savesuffix)

    if anon:
        filename = filename + "-anon"

    if config.savepdf:
        fig.savefig(filename + ".pdf")
    if config.savejpg:
        fig.savefig(filename + ".jpg")
    if config.savepng:
        fig.savefig(filename + ".png")

    plt.close()


################################


def get_col(ph):
    return {"color": ph.get_color()}


################################

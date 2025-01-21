import os
from datetime import datetime, timezone

import ausankey as sky
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import AutoMinorLocator

from .config import Config

############# PARAM ##############


def color_axes(config, ax):
    ax.set_facecolor(config.colors.axis)
    for sp in ax.spines:
        ax.spines[sp].set_color(config.colors.frame)
    ax.tick_params(axis="x", colors=config.colors.frame)
    ax.tick_params(axis="y", colors=config.colors.frame)
    ax.tick_params(labelcolor=config.colors.tick)


def dashboard(config: Config):
    # internal parameters
    # (possibly to generalise later)

    config.expstart = 0

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

    config.retire_yr = config.born_yr + config.retire_age
    ahead_yr = datetime.now(timezone.utc).year + config.future_window
    config.max_yr = min(ahead_yr, config.retire_yr)

    saveprefix = config.saveprefix or os.path.splitext(config.csv)[0]

    datecol = config.strings.datecol
    supercol = config.strings.supercol
    sharescol = config.strings.sharescol
    cashcol = config.strings.cashcol
    expendcol = config.strings.expendcol
    incomecol = config.strings.incomecol

    ############# HELPERS

    errors = {}
    errors["DateColMissing"] = f"One column must be called '{datecol}'."

    def dates_to_years(alldata):
        allcols = alldata.columns.tolist()
        if datecol not in allcols:
            raise RuntimeError(errors.DateColMissing)

        return alldata[datecol].apply(lambda x: datetime.strptime(x, config.datefmt).replace(tzinfo=timezone.utc).year)

    def dates_to_days(data, sincedate):
        days = np.empty(len(data[datecol]))
        for ii, ent in enumerate(data[datecol]):
            y = datetime.strptime(ent, config.datefmt).replace(tzinfo=timezone.utc)
            days[ii] = (y - sincedate).days / 365
        return days

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

    ############# HEADERS

    hdr = pd.read_csv(config.csvdir + config.csv, na_values=0, header=None, nrows=2).transpose()

    hdrnew = {}
    for ii, _ in enumerate(hdr[1]):
        prefix = hdr[0][ii] if isinstance(hdr[0][ii], str) else "_"
        tmpstr = datecol if hdr[1][ii] == datecol else prefix + "_" + hdr[1][ii]
        hdrnew[tmpstr] = hdr[1][ii]
    config.hdrnew = hdrnew

    hdr[1] = list(hdrnew.keys())
    config.super_cols = list(hdr[1][hdr[0] == supercol])
    config.shares_cols = list(hdr[1][hdr[0] == sharescol])
    config.cash_cols = list(hdr[1][hdr[0] == cashcol])
    config.expend_cols = list(hdr[1][hdr[0] == expendcol])
    config.income_cols = list(hdr[1][hdr[0] == incomecol])

    config.super_bool = len(config.super_cols) > 0
    config.shares_bool = len(config.shares_cols) > 0
    config.cash_bool = len(config.cash_cols) > 0
    config.expend_bool = len(config.expend_cols) > 0
    config.income_bool = len(config.income_cols) > 0

    ############# DATA

    alldata = pd.read_csv(config.csvdir + config.csv, na_values=0, header=1)
    alldata = alldata.fillna(0)
    alldata.columns = hdr[1]
    alldata["Year"] = dates_to_years(alldata)

    config.since_yr = config.since_yr or min(alldata.Year)
    config.until_yr = config.until_yr or max(alldata.Year)
    sincedate = datetime(config.since_yr, 1, 1, tzinfo=timezone.utc)
    config.years_until_retire = config.max_yr - config.since_yr
    config.age_at_retire = config.max_yr - config.born_yr

    alldata["Days"] = dates_to_days(alldata, sincedate)
    alldata = alldata.sort_values(by="Days")
    alldata = alldata.reset_index(drop=True)

    alldata["TotalSuper"] = alldata[config.super_cols].sum(axis=1)
    alldata["TotalShares"] = alldata[config.shares_cols].sum(axis=1)
    alldata["TotalCash"] = alldata[config.cash_cols].sum(axis=1)
    alldata["TotalExpend"] = alldata[config.expend_cols].sum(axis=1)
    alldata["TotalIncome"] = alldata[config.income_cols].sum(axis=1)
    alldata["Total"] = alldata["TotalShares"] + alldata["TotalSuper"] + alldata["TotalCash"]

    income_grand_tot = alldata["TotalIncome"].sum()
    income_sum = alldata[config.income_cols].sum()
    income_minor = list(income_sum[income_sum < (1 - config.income_thresh) * income_grand_tot].keys())
    iminor_bool = len(income_minor) > 0

    config.income_minor = income_minor

    config.years_uniq = {}
    for x in alldata["Year"]:
        if x >= config.since_yr and x <= config.until_yr:
            config.years_uniq[x] = True

    data = alldata[alldata.Total > 0]
    data = data.reset_index(drop=True)
    config.window_ind = data.Days > (data.Days.iat[-1] - config.linear_window)

    if config.expend_bool:
        data_sp = alldata[alldata.TotalExpend > 0]
        data_sp = data_sp.reset_index(drop=True)
        config.win_sp_ind = data_sp.Days > (data_sp.Days.iat[-1] - config.linear_window)

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

    ax4 = fig.add_axes([inset_x[0], row_gap + row_y[0] + sankey_h, sankey_w, sankey_h])
    ax5 = fig.add_axes([inset_x[1] - 0.02, row_gap + row_y[0] + sankey_h, sankey_w, sankey_h])

    ax6 = fig.add_axes([inset_x[0], row_y[0], sankey_w, sankey_h])
    ax7 = fig.add_axes([inset_x[1] - 0.02, row_y[0], sankey_w, sankey_h])

    color_axes(config, ax4)
    color_axes(config, ax5)

    if config.expend_bool:
        ax33 = ax3.twinx()
        color_axes(config, ax33)
        ax33.tick_params(axis="y", labelcolor=config.colors.expend)
    else:
        ax33 = ax3

    ########### PANEL 1

    graph_all_vs_time(config, ax1, data)
    panel_total_window(config, ax2, data)

    if config.shares_bool:
        g3 = graph_shares_window(config, ax3, ax33, data, data_sp)
        config.profitloss = g3["profitloss"]
    else:
        config.profitloss = 0

    ############## SANKEY

    panel_income(config, ax4, alldata)

    lbl_font = {"color": config.colors.text, "fontweight": "bold"}

    pc_font = {"color": config.colors.contrast, "fontsize": 10, "rotation": 90, "va": "bottom"}
    if config.shares_bool:
        sky.sankey(
            ax=ax5,
            data=sankey_shares(config, alldata),
            titles=[yrlbl(i) for i in config.years_uniq],
            colormap="Pastel2",
            sort="bottom",
            node_gap=0.00,
            color_dict={"Bought": config.colors.expend, "Growth": config.colors.shares},
            node_width=config.node_width,
            label_loc=["right", "left", "left"],
            label_largest=True,
            label_font=lbl_font,
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

    ax5.axis("on")
    ax5.set_xticklabels(())
    ax5.yaxis.tick_right()
    # ax5.set_xticklabels([i for i in ax5.get_xticklabels()],rotation=90,color=config.colors.tick)
    ax5.yaxis.set_tick_params(which="both", direction="out", right=True, left=True)

    yticks_equalise(config, ax4, ax5)

    if config.income_bool:
        faux_title(config, ax4, "Annual income")
    else:
        ax4.set_yticklabels([])

    if config.anon or (not config.expend_bool):
        faux_title(config, ax5, "Annual shares increase")
    else:
        faux_title(
            config, ax5, "Annual shares increase\nAll-time profit = " + int_to_dollars(config, config.profitloss)
        )

    ######## PANEL 6 ########

    if iminor_bool:
        panel_income_breakdown(config, alldata, ax6)
    else:
        ax6.set_xticklabels([])
        ax6.set_yticklabels([])

    ######## PANEL 7 ########

    if config.shares_bool:
        panel_shares_breakdown(config, data, ax7)
    else:
        color_axes(config, ax7)
        ax7.set_xticklabels([])
        ax7.set_yticklabels([])

    ############## FINISH UP

    if config.anon:
        ax.set_yticklabels([])
        ax2.set_yticklabels([])
        ax3.set_yticklabels([])
        ax33.set_yticklabels([])
        ax4.set_yticklabels([])
        ax5.set_yticklabels([])
        ax.set_ylabel("Amount", color=config.colors.text)
        ax2.set_ylabel("Amount", color=config.colors.text)
        ax3.set_ylabel("Amount", color=config.colors.text)

    plt.show()

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

    plt.close()


############## PANEL 2: Total Window


def graph_all_vs_time(config, ax, data):
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
    tot_growth = extrap_exp(
        ax, data.Days[config.expstart : -1], data.Total[config.expstart : -1], {"color": config.colors.total}
    )

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

    txtstr = "  Total" if config.anon else ("  Total\n  " + int_to_dollars(config, data.Total.iat[-1]))

    ax.text(data.Days.iat[-1], data.Total.iat[-1], txtstr, va="center", color=config.colors.total)

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
            f"Exp growth rate:\n{tot_growth*100:2.1f}% p.a."
            f"\n\nNet worth\nat age {config.age_at_retire}\n= "
            f"{int_to_dollars(config, retire_worth)}"
            f"\n\n{config.retire_ratio:.1%} rule\n= "
            f"{int_to_dollars(config, config.retire_ratio*retire_worth)}"
            f"/yr"
        )
        ax.text(
            data.Days[0],
            0.95 * clim[1],
            txtstr,
            ha="left",
            va="top",
            color=config.colors.total,
        )

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
    ax.plot(rd, yd, "--", lw=config.linewidth / 4, color=config.colors.total)

    ax.set_xlabel(f"Years since {config.since_yr}", color=config.colors.label)
    yticks_dollars(config, ax)

    ax.xaxis.set_minor_locator(AutoMinorLocator(3))
    ax.grid(which="major", color=config.colors.grid, linestyle="-", linewidth=0.5)
    ax.grid(which="minor", color=config.colors.grid, linestyle="-", linewidth=0.5)

    gain = data.Total[config.window_ind].iat[-1] - data.Total[config.window_ind].iat[0]
    elap = data.Days[config.window_ind].iat[-1] - data.Days[config.window_ind].iat[0]

    ax.tick_params(axis="y", labelcolor=config.colors.total)

    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    if config.anon:
        ax.text(
            x_min + 0.05 * (x_max - x_min),
            y_min + 0.95 * (y_max - y_min),
            "Net worth\nincrease",
            color=config.colors.total,
            va="top",
        )
    else:
        peryrtext = "" if config.linear_window == 1 else ("\n" + int_to_dollars(config, gain / elap) + "/yr")
        txtstr = "Net worth\nincrease\n" + int_to_dollars(config, gain) + peryrtext
        ax.text(
            x_min + 0.05 * (x_max - x_min),
            y_min + 0.95 * (y_max - y_min),
            txtstr,
            color=config.colors.total,
            va="top",
            backgroundcolor=config.colors.axis,
        )


def graph_shares_window(config, ax3, ax33, data, data_sp):
    color_axes(config, ax3)
    ax3.plot(
        data.Days[config.window_ind],
        data["TotalShares"][config.window_ind],
        config.marker,
        color=config.colors.shares,
        markersize=config.markersize,
    )
    ax3.set_xlabel(f"Years since {config.since_yr}", color=config.colors.label)

    yticks_dollars(config, ax3)
    ax3.tick_params(axis="y", labelcolor=config.colors.shares)

    ax3.xaxis.set_minor_locator(AutoMinorLocator(3))
    ax3.grid(which="major", color=config.colors.grid, linestyle="-", linewidth=0.5)
    ax3.grid(which="minor", color=config.colors.grid, linestyle="-", linewidth=0.5)

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

    if not config.expend_bool:
        label_graph_shares_a(ax3)
        return {"profitloss": 0}

    sharesum = data_sp["TotalExpend"].cumsum()
    sharebuy = pd.Series(sharesum[config.win_sp_ind]).reset_index(drop=True)
    bought = sharebuy.iat[-1] - sharebuy.iat[0]
    profitloss = shares2.iat[-1] - sharebuy.iat[-1]
    pcgr = 100 * bought / gain

    ax33.plot(
        data_sp.Days[config.win_sp_ind], sharesum[config.win_sp_ind], **config.dotstyle, color=config.colors.expend
    )

    yticks1 = ax3.get_yticks()
    dy = yticks1[1] - yticks1[0]
    yytickx = np.arange(yticks1[0], yticks1[-1] + dy, dy)
    ax3.set_yticks(yytickx)
    ax3.set_ylim(yytickx[0] - dy, yytickx[-1])
    # "-dy" to bump up this line one tick to avoid sometimes clashes with other line
    # ax3.set_yticks()
    yylim1 = ax3.get_ylim()

    yticks2 = ax33.get_yticks()
    ax33.set_ylim(yticks2[0], yticks2[-1])
    yytickx = np.arange(yticks2[0], yticks2[-1] + dy, dy)
    ax33.set_yticks(yytickx)
    ax33.set_ylim(yytickx[0], yytickx[-1])
    yylim2 = ax33.get_ylim()

    yrange = max(yylim1[1] - yylim1[0], yylim2[1] - yylim2[0])

    ax3.set_ylim(yylim1[0], yylim1[0] + yrange)
    ax33.set_ylim(yylim2[0], yylim2[0] + yrange)
    yylim1 = ax3.get_ylim()
    yylim2 = ax33.get_ylim()
    yrange = max(yylim1[1] - yylim1[0], yylim2[1] - yylim2[0])

    yticks_dollars(config, ax3)
    yticks_dollars(config, ax33)
    label_graph_shares_a(ax3)
    label_graph_shares_b(ax3)

    return {"profitloss": profitloss}


############## PANEL 4: Total Window


def panel_income_breakdown(config, data, ax):
    color_axes(config, ax)

    lbl_font = {"color": config.colors.text, "fontweight": "bold"}

    pc_font = {"color": config.colors.contrast, "fontsize": 10, "rotation": 90, "va": "bottom"}

    # TODO: avoid recalc this
    config.years_uniq = {}
    for x in data["Year"]:
        if x >= config.since_yr and x <= config.until_yr:
            config.years_uniq[x] = True

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
        sort="bottom",
        sort_dict=sd,
        node_gap=0.00,
        node_width=config.node_width,
        label_loc=["right", "left", "left"],
        label_font=lbl_font,
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
        sort="bottom",
        node_gap=0.00,
        label_dict=config.hdrnew,
        label_values=not (config.anon),
        label_thresh_ofmax=0.10,
        node_width=config.node_width,
        label_loc=["right", "left", "left"],
        label_largest=True,
        label_font=lbl_font,
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


def panel_income(config, ax4, alldata):
    lbl_font = {"color": config.colors.text, "fontweight": "bold"}

    pc_font = {"color": config.colors.contrast, "fontsize": 10, "rotation": 90, "va": "bottom"}
    if config.income_bool:
        sky.sankey(
            ax=ax4,
            data=sankey_income(config, alldata, config.income_cols),
            titles=[yrlbl(i) for i in config.years_uniq],
            other_thresh_ofsum=config.income_thresh,
            sort="bottom",
            node_gap=0.00,
            node_width=config.node_width,
            label_largest=True,
            label_loc=["right", "left", "left"],
            label_font=lbl_font,
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


################################


def yrlbl(yr):
    yrstr = f"{yr}"
    return "'" + yrstr[2:4]


def yticks_dollars(config, ax):
    ticks = ax.get_yticks()
    ax.set_yticks(ticks)
    newticks = [int_to_dollars(config, int(tick)) for tick in ticks]
    ax.set_yticklabels(newticks)


def int_to_dollars(config, x, plussig=0):
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

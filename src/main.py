
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import ausankey as sky

from .config import Config

############# PARAM ##############





expstart = 0
winyr = 1
targetnext = [1000, 1500, 2000, 3000]

anon = False
figw = 6
figh = 12.5
lw = 1
ms = 4
mm = "."

main_wd = 0.75
main_ht = 0.30
inset_w = 0.35
inset_h = 0.15
sankey_w = 0.375
sankey_h = 0.15

inset_x = [0.1, 0.55]
row_y = [0.05, 0.44, 0.79]
row_gap = 0.03

bgcolor = "#272727"
axiscolor = "#4e4e4e"
textcolor = "white"
lblcolor = textcolor
titlecolor = textcolor
tickcolor = textcolor
dashcolor = "white"
framecolor = "white"
gridcolor = '#b5b5b5'

plotcols = ["#8ec6ff","#ffbf80","#5eff86","#ffa1a1","#e9a8ff"]

node_alpha = 0.8
flow_alpha = 0.5
node_width = 0.15
pc_font = {"color": "black", "fontsize": 10, "rotation": 90}
pc_font5 = {"color": "black", "fontsize": 10, "rotation": 90, "va": "bottom"}

datefmt = '%Y/%m/%d'


def networthdash(config: Config):

    assert config.born_yr, "I can assume your retirement age but not when you were born. please set 'born_yr'."

    retire_yr = min(datetime.now().year + 8,
                    config.born_yr + config.retire_age)

    dotstyle = keyval_to_dict(
                  marker=".",
                  markersize=ms,
                  linestyle="None",
               )
    
    projstyle = keyval_to_dict(
                  linestyle = "-",
                  marker = "None",
                  linewidth = lw/4,
                )
    
    ############# DATA
    
    alldata = pd.read_csv(config.csv,na_values=0)
    alldata = alldata.fillna(0)
    
    allcols = alldata.columns.tolist()
    #print(allcols)
    assert "Date" in allcols, "One column must be called 'Date'."
    
    alldata["Year"] = alldata["Date"].apply(lambda x: 
        datetime.strptime(x, '%Y/%m/%d').year )
        
    since_yr = config.since_yr or min(alldata.Year)

    sincedate = datetime(since_yr, 1, 1)
    years_until_retire = retire_yr - since_yr
    age_at_retirement = retire_yr - config.born_yr

    alldata["Days"] = dates_to_days(alldata,sincedate)
    alldata = alldata.sort_values(by="Days")
    alldata = alldata.reset_index(drop=True)

    income_cols = [*config.income_major,*config.income_minor]

    super = alldata[config.super_cols].sum(axis=1)
    shares = alldata[config.shares_cols].sum(axis=1)
    cash = alldata[config.cash_cols].sum(axis=1)
    total = shares + super + cash
    
    alldata["TotalSuper"] = super
    alldata["TotalShares"] = shares
    alldata["TotalCash"] = cash
    alldata["Total"] = total

    years_uniq = {}
    for x in alldata["Year"]:
      if x >= since_yr:
        years_uniq[x] = True
    
    data = alldata[alldata.Super>0]
    data = data.reset_index(drop=True)
    
    data_sp = alldata[alldata.ShareSpend > 0]
    data_sp = data_sp.reset_index(drop=True)
    
    window_ind = data.Days > (data.Days.iat[-1]-winyr)
    win_sp_ind = data_sp.Days > (data_sp.Days.iat[-1]-winyr)
    
    super = data[config.super_cols].sum(axis=1)
    shares = data[config.shares_cols].sum(axis=1)
    cash = data[config.cash_cols].sum(axis=1)
    total = shares + super + cash
    
    ########### CREATE FIGURE and AXES
    
    fig,ax0 = plt.subplots(figsize=(figw,figh),
                           facecolor=bgcolor)
    ax0.axis("off")
    
    ax1 = fig.add_axes([(1-main_wd)/2, row_y[1], main_wd, main_ht])
    ax = ax1
    ax2 = fig.add_axes([inset_x[0], row_y[2], inset_w, inset_h])
    ax3 = fig.add_axes([inset_x[1], row_y[2], inset_w, inset_h])
    ax6 = fig.add_axes([inset_x[0], row_y[0], sankey_w, sankey_h])
    ax7 = fig.add_axes([inset_x[1]-0.02, row_y[0], sankey_w, sankey_h])
    #ax4 = fig.add_axes([0.1, row_y[0], 0.4, 0.2])
    #ax5 = fig.add_axes([0.5, row_y[0], 0.4, 0.2])
    ax4 = fig.add_axes([inset_x[0], row_gap+row_y[0]+sankey_h, sankey_w, sankey_h])
    ax5 = fig.add_axes([inset_x[1]-0.02, row_gap+row_y[0]+sankey_h, sankey_w, sankey_h])

    color_axes(ax1)
    color_axes(ax2)
    color_axes(ax3)
    color_axes(ax4)
    color_axes(ax5)
    color_axes(ax6)
    color_axes(ax7)

    ########### FITTING and PLOTTING
    
    ax1.set_title("",color=titlecolor)
    ax1.axvline(x=data.Days.iat[-1],
                linestyle="--",color=dashcolor)
    
    def extrap(d,t):
        reg = np.polyfit(d,t,1)
        rd = np.linspace(data.Days[window_ind].iat[0],years_until_retire)
        yd = rd*reg[0] + reg[1]
        return rd, yd

    def extrap_exp(ax,d,t,arg):
        clim = ax.get_ylim()
        logfit = np.polyfit(d,np.log(t),1,w=np.sqrt(t))
        rd = np.linspace(d.iloc[0],years_until_retire)
        yd = np.exp(logfit[1])*np.exp(logfit[0]*rd)
        infl = np.exp(logfit[0])-1
        hp = ax.plot(rd,yd,**(projstyle|arg))
        ax.set_ylim(clim)
        return hp, infl

    rd1, yd1 = extrap(data.Days[window_ind],
                      total[window_ind])
    rd2, yd2 = extrap(data.Days[window_ind],
                      data.Super[window_ind])
    rd3, yd3 = extrap(data.Days[window_ind],
                      shares[window_ind])
    retire_worth = yd1[-1]

    hp1 = ax.plot(rd1,yd1,**projstyle,color=plotcols[0])
    hp2 = ax.plot(rd2,yd2,**projstyle,color=plotcols[1])
    hp3 = ax.plot(rd3,yd3,**projstyle,color=plotcols[2])

    hp11, tot_growth = extrap_exp(ax,
        data.Days[expstart:-1],
        total[expstart:-1],
        get_col(hp1[0])
    )

    ind = data.Super[expstart:-1]> 0
    days = data.Days[expstart:-1][ind]
    val = data.Super[expstart:-1][ind]
    hp22 = extrap_exp(ax,days,val,get_col(hp2[0]))

    ind = shares[expstart:-1]> 0
    days = data.Days[expstart:-1][ind]
    val = shares[expstart:-1][ind]
    hp33 = extrap_exp(ax,days,val,get_col(hp3[0]))
    ax.plot(data.Days,total,
      **get_col(hp1[0]),**dotstyle)
    ax.plot(data.Days,shares,
      color = hp3[0].get_color(),**dotstyle)
    ax.plot(data.Days,data.Super,
      **get_col(hp2[0]),**dotstyle)
    hp4 = ax.plot(data.Days,cash,
      **dotstyle,color=plotcols[3])
    
    ############% LABELS
    
    va = "center"
    ax.text(data.Days.iat[-1],cash.iat[-1],
      "  Cash",color=hp4[0].get_color(),va=va)
    ax.text(data.Days.iat[-1],shares.iat[-1],
      "  Shares",color=hp3[0].get_color(),va=va)
    ax.text(data.Days.iat[-1],super.iat[-1],
      "  Super",color=hp2[0].get_color(),va=va)
    
    if anon:
        str = "  Total"
    else:
        str = f"  Total\n  ${total.iat[-1]/1000:0.3f}M"
    
    ax.text(
        data.Days.iat[-1],total.iat[-1],
        str,
        va="center",
        color=hp1[0].get_color())
    
    ax.set_xticks(range(years_until_retire+1))
    ax.set_xticklabels(range(since_yr,since_yr + years_until_retire+1),rotation=90,color=tickcolor)
    clim = ax.get_ylim()
    ax.set_ylim(0,clim[1])
    yticks_M(ax1)
    ax.set_ylim(0,clim[1])

    if not anon:
        ax.text(data.Days[0],0.95*clim[1],
            f"Exp growth rate:\n{tot_growth*100:2.1f}% p.a.\n\nNet worth\nat age {age_at_retirement}\n= \${retire_worth/1000:3.2f}M;\n\n3% rule\n= \${0.03*retire_worth:1.0f}k/yr",
            ha = "left",
            va = "top",
            color = textcolor,
        )
    
    #######%%###### EXTRAP
    
    def extrap_target(yy):
        reg = np.polyfit(data.Days[window_ind],total[window_ind],1)
    
        rr = (yy - reg[1])/reg[0]
        
        ax.plot((rr,rr,data.Days.iat[-1]),(0,yy,yy),'-',lw=lw,color="#b6b6b6")
        
        ax.text( data.Days.iat[-1] + (rr-data.Days.iat[-1])/2 , yy*0.99 , f"{round(rr-data.Days.iat[-1],1)} yrs" , ha="center", va="top", color = textcolor)
        ax.text( data.Days.iat[-1] + (rr-data.Days.iat[-1])/2 , yy*1.01 , f"${yy/1000}M" , ha="center", va="bottom", color = textcolor)
        
    if not anon:
        for ii in targetnext:
            if ii < 0.85*ax.get_ylim()[1]:
                extrap_target(ii)
            
            
    ############## INSET
    
    reg = np.polyfit(data.Days[window_ind],total[window_ind],1)
    rd = np.linspace(data.Days[window_ind].iat[0],data.Days.iat[-1])
    yd = rd*reg[0] + reg[1]
    ax2.plot(rd,yd,"-",lw=lw,color=hp1[0].get_color())
    ax2.plot(
        data.Days[window_ind],total[window_ind],
        **get_col(hp1[0]),**dotstyle)
    
    logfit = np.polyfit(data.Days[window_ind],np.log(total[window_ind]),1,w=np.sqrt(total[window_ind]))
    rd = np.linspace(data.Days[window_ind].iat[0],data.Days.iat[-1])
    yd = np.exp(logfit[1])*np.exp(logfit[0]*rd)
    ax2.plot(rd,yd,"--",lw=lw,color=hp11[0].get_color())
    
    ax2.set_xlabel(f"Years since {since_yr}",color=lblcolor)
    yticks_k(ax2,2)
    
    
    
    ax2.xaxis.set_minor_locator(AutoMinorLocator(3)) 
    ax2.grid(which='major', color=gridcolor, linestyle='-', linewidth=0.5)
    ax2.grid(which='minor', color=gridcolor, linestyle='-', linewidth=0.5)
    
    gain = total[window_ind].iat[-1]-total[window_ind].iat[0]
    elap = data.Days[window_ind].iat[-1]-data.Days[window_ind].iat[0]
    
    ax2.tick_params(axis="y",labelcolor=hp1[0].get_color())
    
    x_min, x_max = ax2.get_xlim()
    y_min, y_max = ax2.get_ylim()
    
    if anon:
        ax2.text(
              x_min+0.05*(x_max-x_min) ,
              y_min+0.95*(y_max-y_min) ,
              f"Net worth\nincrease",
              color=hp1[0].get_color(),
              va = "top")
    else:
        if winyr == 1:
            peryrtext = ""
        else:
            peryrtext = f"\n\${gain/elap:1.0f}k/yr"
        ax2.text(
              x_min+0.05*(x_max-x_min) ,
              y_min+0.95*(y_max-y_min) ,
              f"Net worth\nincrease\n\${gain:3.0f}k" + peryrtext,
              color=hp1[0].get_color(),
              va = "top",
              backgroundcolor = axiscolor)
    
    
    ############## INSET 2
    
    ax3.plot(
        data.Days[window_ind],shares[window_ind],
        ".",color=hp3[0].get_color(),markersize=ms)
    ax3.set_xlabel(f"Years since {since_yr}",color=lblcolor)
    
    ax33 = ax3.twinx()
    color_axes(ax33)

    sharesum = data_sp.ShareSpend.cumsum()
    hp7 = ax33.plot(
        data_sp.Days[win_sp_ind],sharesum[win_sp_ind],
        **dotstyle,color=plotcols[4])
    
    yticks1 = ax3.get_yticks()
    yticks2 = ax33.get_yticks()
    
    dy = yticks1[1]-yticks1[0]
    ax3.set_ylim(yticks1[0]-dy,yticks1[-1]) # "-dy" to bump up this line one tick to avoid sometimes clashes with other line
    ax33.set_ylim(yticks2[0],yticks2[-1])
    
    yylim1 = ax3.get_ylim()
    yylim2 = ax33.get_ylim()
    
    yrange = max(yylim1[1]-yylim1[0],
                 yylim2[1]-yylim2[0])
    
    ax3.set_ylim(  yylim1[0], yylim1[0] + yrange )
    ax33.set_ylim( yylim2[0], yylim2[0] + yrange )
    
    yticks1 = ax3.get_yticks()
    yticks2 = ax33.get_yticks()

    yticks_k(ax3,2)
    yticks_k(ax33,2)

    ax3.set_ylim(  yylim1[0], yylim1[0] + yrange )
    ax33.set_ylim( yylim2[0], yylim2[0] + yrange )
    ax3.tick_params(axis="y",labelcolor=hp3[0].get_color())
    ax33.tick_params(axis="y",labelcolor=hp7[0].get_color())
    
    ax3.xaxis.set_minor_locator(AutoMinorLocator(3)) 
    ax3.grid(which='major', color='#b5b5b5', linestyle='-', linewidth=0.5)
    ax3.grid(which='minor', color='#b5b5b5', linestyle='-', linewidth=0.5)
    
    shares2 = pd.Series(shares[window_ind]).reset_index(drop=True)
    sharebuy = pd.Series(sharesum[win_sp_ind]).reset_index(drop=True)
    pcgr = 100*(sharebuy.iat[-1] - sharebuy.iat[1])/(shares2.iat[-1] - shares2.iat[1])

    profitloss = shares2.iat[-1] - sharebuy.iat[-1]
    gain = shares2.iat[-1] - shares2.iat[1]
    elap = data.Days[window_ind].iat[-1]-data.Days[window_ind].iat[0]

    x_min, x_max = ax3.get_xlim()
    y_min, y_max = ax3.get_ylim()
    if anon:
        ax3.text( 
              x_min+0.05*(x_max-x_min) ,
              y_min+0.95*(y_max-y_min) ,
              f"Shares\nincrease",
              color=hp3[0].get_color(),
              va = "top",
              backgroundcolor = axiscolor)
    else:
        if winyr == 1:
            peryrtext = ""
        else:
            peryrtext = f"\n\${gain/elap:1.0f}k/yr"
        ax3.text( 
              x_min+0.05*(x_max-x_min) ,
              y_min+0.95*(y_max-y_min) ,
              f"Shares\nincrease\n\${gain:2.0f}k" + peryrtext,
              color=hp3[0].get_color(),
              va = "top",
              backgroundcolor = axiscolor)
    
    if anon:
        ax3.text( 
              x_min+0.95*(x_max-x_min) ,
              y_min+0.05*(y_max-y_min) ,
              f"Purchased =\n{pcgr:2.0f}% of growth",
              color=hp7[0].get_color(),
              ha = "right",
              backgroundcolor = axiscolor)
    else:
        ax3.text( 
              x_min+0.95*(x_max-x_min) ,
              y_min+0.05*(y_max-y_min) ,
              f"Bought \${sharebuy.iat[-1] - sharebuy.iat[1]:2.0f}k\n{pcgr:2.0f}% of growth",
              color=hp7[0].get_color(),
              ha = "right",
              backgroundcolor = axiscolor)
     

    ############## SANKEY SETUP
    
    def get_inc_totals(data,income_cols):
        total = {}
        for col in income_cols:
          total[col] = sum(data[col])
        return total

    def get_shares_totals(data,cols):
        total = {}
        for col in cols:
          total[col] = list(data[col])[-1]
        return total
    
    def sankey_income(data,income_cols):
        total_by_yr = {}
        for yr in years_uniq.keys():
            total_by_yr[f"f{yr}"] = income_cols
            total_by_yr[yr] = get_inc_totals(
                data[data["Year"] == yr],
                income_cols
            ).values()
        return pd.DataFrame(total_by_yr)
    
    def get_totals(data,val,spend):
        shares = data[data[val]>0]
        total = {}
        total['Bought'] = sum(data[spend])
        total['Growth'] = max(shares[val]) - min(shares[val]) - sum(data[spend])
        return total
    
    def sankey_shares(data):
        total_by_yr = {}
        for yr in years_uniq.keys():
            total_by_yr[f"f{yr}"] = ['Bought','Growth']
            total_by_yr[yr] = get_totals(
                data[data["Year"] == yr],
                "TotalShares","ShareSpend"
            ).values()
        return pd.DataFrame(total_by_yr)
    
    def sankey_shares_makeup(data):
        total_by_yr = {}
        for yr in years_uniq.keys():
            total_by_yr[f"f{yr}"] = config.shares_cols
            total_by_yr[yr] = get_shares_totals(
                data[data["Year"] == yr],
                config.shares_cols
            ).values()
        return pd.DataFrame(total_by_yr)
    
    ############## SANKEY INCOME
    
    sky.sankey(ax=ax4,
       data=sankey_income(alldata,income_cols),
       titles=[(i) for i in years_uniq],
       other_thresh_val=10000,
       sort = "bottom" ,
       node_gap=0.00,
       node_width = node_width,
       label_loc = ["none","none","left"],
       label_font = {"color": textcolor},
       value_loc = ["none","none","none"],
       node_alpha = node_alpha,
       flow_alpha = flow_alpha,
       title_side = "none",
       percent_loc = "center",
       percent_loc_ht = 0.05,
       percent_font = pc_font5,
       percent_thresh = 0.2,
       colormap = "Set3",
       label_values = not(anon),
       value_fn = lambda x: f"\n${x/1000:1.1f}k" ,
      )

    ssdata = sankey_income(alldata,config.income_minor)
    sdata = ssdata.iloc[:,-2:]
    sdata = sdata.set_index(sdata.columns[0])
    ssort = sdata.to_dict(orient="dict")
    sd = ssort[list(ssort.keys())[0]]
    sky.sankey(ax=ax6,
       data=ssdata,
       titles=[(i) for i in years_uniq],
       other_thresh_val=100,
       sort = "bottom",
       sort_dict = sd,
       node_gap=0.00,
       node_width = node_width,
       label_loc = ["none","none","left"],
       label_font = {"color": textcolor},
       label_dict = {"Dividend": "Div", "dVDHG": "VDHG"},
       value_loc = ["center","center","center"],
       node_alpha = node_alpha,
       flow_alpha = flow_alpha,
       title_side = "none",
       percent_loc = ("none","none","center"),
       percent_font = pc_font,
       percent_thresh = 0.2,
       percent_thresh_val = 1000,
       label_thresh = 1500,
       label_values = not(anon),
       colormap="Pastel2",
       value_fn = lambda x: f"\n${x/1000:1.1f}k" ,
      )

    sky.sankey(ax=ax5,data=sankey_shares(alldata),
       titles=[(i) for i in years_uniq],
       colormap="Pastel2",
       sort = "bottom" ,
       node_gap=0.00,
       color_dict = {"Bought": plotcols[4], "Growth": plotcols[2]},
       node_width = node_width,
       label_loc = ["none","none","left"],
       label_font = {"color": textcolor},
       value_loc = ["none","none","none"],
       node_alpha = node_alpha,
       flow_alpha = flow_alpha,
       title_side = "none",
       percent_loc = "center",
       percent_loc_ht = 0.05,
       percent_font = pc_font5,
       percent_thresh = 0.2,
       percent_thresh_val = 20,
       label_values = not(anon),
       value_fn = lambda x: f"\n${x:1.1f}k" ,
      )

    sky.sankey(ax=ax7,data=sankey_shares_makeup(alldata),
       titles=[(i) for i in years_uniq],
       colormap="Pastel1",
       sort = "bottom" ,
       node_gap=0.00,
       label_dict = {"sVDHG": "VDHG","sAAPL": "AAPL"},
       label_values = not(anon),
       label_thresh = 20,
       node_width = node_width,
       label_loc = ["none","none","left"],
       label_font = {"color": textcolor},
       value_loc = ["none","none","none"],
       value_fn = lambda x: f"\n${round(x)}k",
       node_alpha = node_alpha,
       flow_alpha = flow_alpha,
       title_side = "none",
       percent_loc = "center",
       percent_loc_ht = 0.5,
       percent_font = pc_font,
       percent_thresh = 0.20,
       percent_thresh_val = 50,
      )

    def faux_title(ax,str):
        xrange = np.diff(ax.get_xlim())
        ax.text(
            ax.get_xlim()[0] + 0.02 * xrange,
            0.95*ax.get_ylim()[1],
            str,
            color=titlecolor,
            ha="left",
            va="top",
        )
    

    ax4.axis("on")
    ax5.axis("on")
    ax6.axis("on")
    ax7.axis("on")
    
    ymax = max(ax4.get_ylim()[1],ax5.get_ylim()[1]*1000)
    ax4.set_ylim([0,ymax])
    ax5.set_ylim([0,ymax/1000])
    ax6.set_ylim([0,ax6.get_ylim()[1]])
    ax7.set_ylim([0,ax7.get_ylim()[1]])
    
    ax4.set_yticks(ax4.get_yticks())
    ax6.set_yticks(ax6.get_yticks())
    ax7.set_yticks(ax7.get_yticks())
    
    ax5.set_yticks([tick/1000 for tick in ax4.get_yticks()])

    ax4.set_xticklabels(())
    ax4.set_yticklabels([f'${int(tick/1000)}k' for tick in ax4.get_yticks()])
    ax6.set_yticklabels([f'${int(tick/1000)}k' for tick in ax6.get_yticks()])

    ax5.set_xticklabels(())
    ax5.yaxis.tick_right()
    ax7.yaxis.tick_right()
    ax5.set_yticklabels([f'${int(tick/1000)}k' for tick in ax4.get_yticks()])
    ax7.set_yticklabels([f'${int(tick)}k' for tick in ax7.get_yticks()])
    
    #ax4.set_xticklabels([i for i in ax4.get_xticklabels()],rotation=90,color=tickcolor)
    #ax5.set_xticklabels([i for i in ax5.get_xticklabels()],rotation=90,color=tickcolor)
    
    ax4.yaxis.set_tick_params(which='both', direction='out', right=True, left=True)
    ax5.yaxis.set_tick_params(which='both', direction='out', right=True, left=True)
    ax7.yaxis.set_tick_params(which='both', direction='out', right=True, left=True)
    
    faux_title(ax4,"Annual income")
    if anon:
        faux_title(ax5,f"Annual shares increase")
    else:
        faux_title(ax5,f"Annual shares increase\nAll-time profit = +${profitloss:1.1f}k")
    faux_title(ax6,"'Other' income breakdown")
    faux_title(ax7,"Shares breakdown")
    
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
        ax.set_ylabel("Amount",color=textcolor)
        ax2.set_ylabel("Amount",color=textcolor)
        ax3.set_ylabel("Amount",color=textcolor)
    
    
    plt.show()
    
    filename = config.savedir + ".wr-net-worth-"+datetime.now().strftime("%Y-%m")
    if anon:
        filename = filename + "-anon"
    
    fig.savefig(filename+".pdf")
    fig.savefig(filename+".jpg")
    
    plt.close()


############# HELPERS

def color_axes(ax):
    ax.set_facecolor(axiscolor)
    for sp in ax.spines:
        ax.spines[sp].set_color(framecolor)
    ax.tick_params(axis='x', colors=framecolor)
    ax.tick_params(axis='y', colors=framecolor)
    ax.tick_params(labelcolor=tickcolor)

def dates_to_days(data,sincedate):
    N = len(data.Date)
    days = np.empty(N)
    for ii,ent in enumerate(data.Date):
        y = datetime.strptime(ent, datefmt)
        days[ii] = (y-sincedate).days / 365
    return days

################################

def yticks_M(ax,n=2):
    ax.set_yticks(ax.get_yticks())
    if n == 1:
        ax.set_yticklabels([f'${(tick/1000):1.1f}M' for tick in ax.get_yticks()])
    if n == 2:
        ax.set_yticklabels([f'${(tick/1000):1.2f}M' for tick in ax.get_yticks()])

def yticks_k(ax,n=0):
    ax.set_yticks(ax.get_yticks())
    ax.set_yticklabels([f'${int(tick)}k' for tick in ax.get_yticks()])

################################

def keyval_to_dict(**kwargs):
    return kwargs

def get_col(ph):
    return {"color": ph.get_color()}

################################

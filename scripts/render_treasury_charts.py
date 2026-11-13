"""Render a coordinated presentation of existing Treasury chart data.

No data acquisition, estimation, or research-source mutation occurs here. Existing
CSV values and saved annual-regression coefficients are the sole numerical inputs.
Original images and datasets remain unchanged. Run from any directory with Python,
matplotlib, numpy and pandas installed.
"""
from pathlib import Path
import os
import hashlib
import json
os.environ.setdefault('MPLCONFIGDIR', '/tmp/nicholas-treasury-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/treasury-2026-11'
OUT.mkdir(parents=True, exist_ok=True)
BG, FG, MUTED, GRID, REF = '#0d1117', '#e6edf3', '#9da7b3', '#29323d', '#c6cdd5'
BLUE, TEAL, AMBER = '#79b8f3', '#67c5b4', '#ddb66e'
plt.rcParams.update({
    'font.family':'DejaVu Sans', 'font.size':18, 'axes.labelsize':18,
    'xtick.labelsize':18, 'ytick.labelsize':18, 'text.color':FG,
    'axes.labelcolor':MUTED, 'xtick.color':MUTED, 'ytick.color':MUTED,
    'figure.facecolor':BG, 'axes.facecolor':BG, 'savefig.facecolor':BG,
    'svg.fonttype':'none', 'svg.hashsalt':'nicholas-treasury-2026-11',
    'path.simplify':False, 'lines.solid_capstyle':'round',
})
FILES = {
 'a1-premium-balance':'assets/term-premium/2026-10/fig1_premium_and_balance.csv',
 'a1-estimates':'assets/term-premium/2026-10/fig2_estimates.csv',
 'a1-fiscal-years':'assets/term-premium/2026-10/fig3_fiscal_years.csv',
 'a1-two-models':'assets/term-premium/2026-10/fig4_two_models.csv',
 'lab-spec-curve':'assets/term-premium/lab-2026-10/exp1-curve.csv',
 'lab-baseline':'assets/term-premium/lab-2026-10/exp2c-baseline.csv',
 'tic-lt-official-private':'assets/tic-2026-11/tic-lt-official-private.csv',
 'tic-official-share-by-maturity':'assets/tic-2026-11/tic-official-share-by-maturity.csv',
}
provenance = {'purpose':'Presentation only; no estimation or numerical-source edits.',
 'palette':{'background':BG,'foreground':FG,'muted':MUTED,'primary':BLUE,'comparison':TEAL,'third':AMBER},
 'charts':{}, 'checks':{}}
hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES.values()}
RESULTS = 'assets/term-premium/2026-10/results.json'
hashes[RESULTS] = hashlib.sha256((ROOT/RESULTS).read_bytes()).hexdigest()

def data(name):
    d = pd.read_csv(ROOT / FILES[name])
    provenance['charts'][name] = {'source':FILES[name], 'source_sha256':hashes[FILES[name]], 'rows':len(d)}
    return d

def canvas(height=6.0, left=.065, top=.80, bottom=.14, right=.85):
    fig = plt.figure(figsize=(8.6,height),dpi=200)
    ax = fig.add_axes([left,bottom,right-left,top-bottom])
    style(ax)
    return fig,ax

def style(ax, horizontal=True):
    ax.set_axisbelow(True)
    for side in ('top','left','right'): ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color(MUTED)
    ax.spines['bottom'].set_linewidth(.7)
    ax.tick_params(axis='both',length=0,pad=10)
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position('right')
    ax.grid(axis='y' if horizontal else 'x',color=GRID,lw=.7)

def ticks(ax, vals, unit='', money=False):
    ax.set_yticks(vals)
    def fmt(x,_):
        val=f'{x:,.0f}'.replace('-', '−')
        return (('$' if money else '')+val+unit) if x==max(vals) else val
    ax.yaxis.set_major_formatter(FuncFormatter(fmt))

def legend(fig, items, y=.94, fontsize=18, ncol=2):
    handles=[]
    for label,color,ls,marker in items:
        handles.append(Line2D([],[],color=color,lw=3,linestyle=ls,marker=marker,
                              markersize=7,label=label))
    fig.legend(handles=handles,loc='upper left',bbox_to_anchor=(.055,y),
               ncol=ncol,frameon=False,fontsize=fontsize,handlelength=1.25,
               handletextpad=.5,columnspacing=1.15,labelcolor=FG,borderaxespad=0)

def callout(ax,x,y,label,xytext,color=FG,ha='left',va='center',fontsize=16):
    ax.scatter([x],[y],s=25,color=color,zorder=6)
    ax.annotate(label,xy=(x,y),xytext=xytext,textcoords='data',ha=ha,va=va,
                color=color,fontsize=fontsize,
                arrowprops={'arrowstyle':'-','color':color,'lw':.8,'shrinkA':6,'shrinkB':5},
                bbox={'facecolor':BG,'edgecolor':'none','pad':2.5,'alpha':.94},zorder=7)

def save(fig,name):
    fig.canvas.draw()
    fig.savefig(OUT/(name+'.png'),dpi=200)
    fig.savefig(OUT/(name+'.svg'),metadata={'Date':None,'Creator':'Treasury presentation renderer'})
    provenance['charts'][name]['dimensions_px']=[round(fig.get_figwidth()*200),round(fig.get_figheight()*200)]
    plt.close(fig)

def date_axis(ax,start,end,ticks_):
    ax.set_xlim(pd.Timestamp(start),pd.Timestamp(end))
    ax.set_xticks([pd.Timestamp(f'{y}-01-01') for y in ticks_])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

def premium_balance():
    name='a1-premium-balance';d=data(name);d['date']=pd.to_datetime(d.date)
    fig=plt.figure(figsize=(8.6,8.5),dpi=200)
    a=fig.add_axes([.065,.56,.78,.34]);b=fig.add_axes([.065,.11,.78,.33])
    for ax in (a,b):
        style(ax);date_axis(ax,'1979-01-01','2027-05-01',[1980,1990,2000,2010,2020])
        ax.axvline(pd.Timestamp('2008-01-01'),color=MUTED,lw=.9,ls=(0,(2,3)),alpha=.65)
        ax.axhline(0,color=REF,lw=1)
    a.plot(d.date,d.acm_tp10,color=BLUE,lw=1.8);a.set_ylim(-1.6,5.3);ticks(a,[-1,0,2,4],'%')
    a.set_xticklabels([])
    fig.text(.065,.94,'ACM 10-year term premium',fontsize=20)
    k=d.index[d.date.dt.to_period('M')==pd.Period('2008-01','M')][0]
    callout(a,d.date.iloc[k],d.acm_tp10.iloc[k],'January 2008:\ncomparison date',
            (pd.Timestamp('2009-05-01'),3.45),fontsize=17)
    b.step(d.date,d.balance_fy,color=TEAL,lw=2,where='post');b.set_ylim(-16,3);ticks(b,[-15,-10,-5,0],'%')
    fig.text(.065,.49,'Fiscal balance, share of GDP',fontsize=20)
    fig.text(.065,.035,'Deficits are below zero',fontsize=17,color=MUTED)
    provenance['charts'][name]['notes']='Both source columns plotted; missing fiscal values are left missing. January 2008 is a comparison-date annotation.'
    save(fig,name)

def estimates():
    name='a1-estimates';d=data(name)
    labels=['Saved\nbaseline','Fiscal-year\ntiming','36-month\nuncertainty','One row per\nfiscal year','Inflation and\noutput gap','Kim–Wright\n(from 1990)']
    fig,ax=canvas(8.0,left=.31,right=.94,top=.85,bottom=.16)
    style(ax,False);ax.yaxis.grid(False);ax.yaxis.tick_left();ax.spines['bottom'].set_visible(False)
    for j,spec in enumerate(d.spec.unique()):
        sub=d[d.spec==spec]
        for period,color,marker,offset in [('1980-2007',BLUE,'o',-.16),('2008 onward',TEAL,'s',.16)]:
            r=sub[~sub.period.str.startswith('2008')] if period=='1980-2007' else sub[sub.period.str.startswith('2008')]
            assert len(r)==1,(spec,period)
            r=r.iloc[0]; y=j+offset
            ax.errorbar(r.bp,y,xerr=[[r.bp-r.lo],[r.hi-r.bp]],fmt=marker,color=color,
                        lw=2,ms=6,mec=BG,mew=1.1,capsize=0,zorder=3)
    ax.axvline(0,color=REF,lw=1.1);ax.set_xlim(-10,44);ax.set_ylim(5.6,-.6)
    ax.set_yticks(range(6),labels,fontsize=17);ax.set_xticks([0,10,20,30,40]);ax.tick_params(axis='y',pad=15)
    legend(fig,[('Before 2008',BLUE,'-','o'),('2008 onward',TEAL,'-','s')],y=.97,ncol=2,fontsize=17)
    fig.text(.065,.055,'Basis points per 1 point of GDP wider deficit',fontsize=17)
    fig.text(.065,.02,'Dots and squares: estimates · Lines: 95% intervals',fontsize=15,color=MUTED)
    provenance['charts'][name]['checks']={'estimates':len(d),'intervals':len(d),'specifications':d.spec.nunique()}
    save(fig,name)

def fiscal_years():
    name='a1-fiscal-years';d=data(name);r=json.loads((ROOT/RESULTS).read_text())['specs']['fy_annual_hc1']
    fig,ax=canvas(6.6,top=.78,bottom=.19,right=.86)
    for period,color,marker in [('pre',BLUE,'o'),('post',TEAL,'s')]:
        s=d[d.period==period];x=s.balance_fy.to_numpy();y=s.acm_tp10_debt_adjusted.to_numpy()
        ax.scatter(x,y,color=color,marker=marker,s=34,zorder=3)
        slope=r[period]['coef'];intercept=float(y.mean()-slope*x.mean())
        xx=np.array([x.min(),x.max()]);ax.plot(xx,intercept+slope*xx,color=color,lw=1.6)
    ax.axhline(0,color=REF,lw=1);ax.axvline(0,color=MUTED,lw=.8)
    ax.set_ylim(-.9,4.45);ax.set_xlim(-15.5,3);ticks(ax,[0,1,2,3,4],'%');ax.set_xticks([-15,-10,-5,0])
    legend(fig,[('1981–2007',BLUE,'','o'),('2008–2025',TEAL,'','s')],y=.97,fontsize=18)
    fig.text(.065,.855,'Debt-adjusted 10-year term premium',fontsize=17,color=MUTED)
    positions={1983:(-8.5,3.2),1992:(-5.0,4.3),2000:(1.0,2.5),2009:(-12.5,1.45),2020:(-14.6,-.67),2024:(-8.0,-.65)}
    for year,pos in positions.items():
        row=d[d.fiscal_year==year].iloc[0]
        callout(ax,row.balance_fy,row.acm_tp10_debt_adjusted,str(year),pos,fontsize=15,color=MUTED)
    fig.text(.065,.07,'Fiscal balance, % of GDP (deficit below 0)',fontsize=17)
    provenance['charts'][name]['fit_line']='Existing fy_annual_hc1 slopes; lines centered on each plotted group mean. No model refit.'
    provenance['charts'][name]['additional_source']={'path':RESULTS,'sha256':hashes[RESULTS]}
    provenance['charts'][name]['points']={'pre':int((d.period=='pre').sum()),'post':int((d.period=='post').sum())}
    save(fig,name)

def two_models():
    name='a1-two-models';d=data(name);d['date']=pd.to_datetime(d.date)
    fig,ax=canvas(6.0,top=.80)
    ax.plot(d.date,d.acm_tp10,color=BLUE,lw=1.9)
    ax.plot(d.date,d.kw_tp10,color=TEAL,lw=1.8,ls=(0,(6,2)))
    legend(fig,[('ACM',BLUE,'-',None),('Kim–Wright',TEAL,'--',None)])
    ax.axhline(0,color=REF,lw=1);ax.set_ylim(-1.7,4.3);ticks(ax,[-1,0,1,2,3,4],'%')
    date_axis(ax,'1989-01-01','2027-01-01',[1990,2000,2010,2020])
    save(fig,name)

def specification_curve():
    name='lab-spec-curve';d=data(name);fig,ax=canvas(6.8,top=.78,bottom=.17)
    ax.vlines(d['rank'],d.change_bp_lo,d.change_bp_hi,color=BLUE,alpha=.22,lw=.45)
    ax.plot(d['rank'],d.change_bp,color=BLUE,lw=2.2)
    ax.axhline(0,color=REF,lw=1.15);ax.set_ylim(-70,55);ticks(ax,[-50,-25,0,25,50],' bp')
    ax.set_xlim(1,1050);ax.set_xticks([1,250,500,750,1050])
    fig.text(.065,.95,'Change in the deficit link',fontsize=20)
    fig.text(.065,.885,'Basis points per 1 point of GDP',fontsize=17,color=MUTED)
    baseline=d[d.article1.astype(str).str.lower()=='true'];assert len(baseline)==1
    p=baseline.iloc[0];ax.scatter([p['rank']],[p.change_bp],s=75,marker='D',color=AMBER,edgecolor=BG,zorder=5)
    ax.annotate('Main specification',xy=(p['rank'],p.change_bp),xytext=(470,-48),
                color=FG,fontsize=16,arrowprops={'arrowstyle':'-','color':AMBER,'lw':1})
    fig.text(.065,.075,'1,050 specifications, sorted by estimated change',fontsize=16)
    fig.text(.065,.025,'Line: estimate · Thin bars: 95% intervals',fontsize=16,color=MUTED)
    provenance['charts'][name]['checks']={'estimates':len(d),'intervals':len(d),'main_specifications':len(baseline)}
    save(fig,name)

def baseline_paths():
    name='lab-baseline';d=data(name);fig,ax=canvas(7.0,top=.72,bottom=.15)
    for version,color in [('C0',BLUE),('C1',TEAL)]:
        s=d[(d.series=='path')&(d.version==version)].sort_values('fiscal_year')
        assert len(s)==56,(version,len(s))
        ax.plot(s.fiscal_year,s.smoothed_bp,color=color,lw=2.1,ls='-' if version=='C0' else (0,(6,2)))
        if version=='C0':
            ax.plot(s.fiscal_year,s.smoothed_bp_lo,color=color,lw=1,ls=(0,(3,3)),alpha=.8)
            ax.plot(s.fiscal_year,s.smoothed_bp_hi,color=color,lw=1,ls=(0,(3,3)),alpha=.8)
        else: ax.fill_between(s.fiscal_year,s.smoothed_bp_lo,s.smoothed_bp_hi,color=color,alpha=.15)
    legend(fig,[('Fixed baseline',BLUE,'-',None),('Drifting baseline',TEAL,'--',None)],y=.97,fontsize=17)
    fig.text(.065,.875,'95% uncertainty: dashed bounds / shaded band',fontsize=15,color=MUTED)
    ax.set_xlim(1968,2028);ax.set_ylim(-45,86);ticks(ax,[-25,0,25,50,75],' bp');ax.set_xticks([1970,1990,2010,2025])
    ax.axhline(0,color=REF,lw=1)
    events=d[d.series=='event']
    # Staggered numbered markers retain all event dates without assigning them causal meaning.
    heights={1:.02,2:.055,3:.10,4:.02,5:.06,6:.145,7:.02,8:.10,9:.145,10:.02,11:.10,12:.18,13:.02}
    for _,r in events.iterrows():
        n=int(r.id);x=float(r.fiscal_year_position)
        ax.axvline(x,color=MUTED,lw=.65,ls=(0,(2,3)),alpha=.27)
        ax.text(x,1+heights[n],str(n),transform=ax.get_xaxis_transform(),ha='center',color=MUTED,fontsize=12,clip_on=False)
    fig.text(.065,.06,'Fiscal year · Smoothed paths',fontsize=17)
    fig.text(.065,.015,'Numbered dates match the events in the caption',fontsize=15,color=MUTED)
    provenance['charts'][name]['checks']={'path_rows':int((d.series=='path').sum()),'event_markers':len(events),'uncertainty_bounds':'All C0 and C1 smoothed 95% bounds retained.'}
    save(fig,name)

def ownership_levels():
    name='tic-lt-official-private';d=data(name);fig,ax=canvas(6.3,top=.80,bottom=.14,right=.81)
    ax.plot(d.year,d.official_bn,color=BLUE,lw=2.1)
    ax.plot(d.year,d.private_bn,color=TEAL,lw=2.1,ls=(0,(6,2)))
    legend(fig,[('Foreign official',BLUE,'-',None),('Foreign private',TEAL,'--',None)],fontsize=16.5)
    ax.set_xlim(2007.7,2025.5);ax.set_ylim(0,5200);ticks(ax,[0,1000,2000,3000,4000,5000],'bn',money=True)
    ax.set_xticks([2008,2013,2018,2025]);ax.axhline(0,color=REF,lw=.9)
    callout(ax,2025,4165,'Private exceeds\nofficial in 2025',(2016.5,4760),color=FG,fontsize=16)
    save(fig,name)

def ownership_shares():
    name='tic-official-share-by-maturity';d=data(name);fig,ax=canvas(6.6,top=.75,bottom=.14)
    for maturity,color,ls in [('long_term',BLUE,'-'),('all',TEAL,'--'),('short_term',AMBER,':')]:
        # The exported source calls the combined category all_maturities.
        s=d[d.maturity.isin([maturity,'all_maturities'] if maturity=='all' else [maturity])]
        assert len(s)==18,(maturity,len(s))
        ax.plot(s.year,s.official_share_pct,color=color,lw=2.1,ls=ls)
    legend(fig,[('Long-term',BLUE,'-',None),('All maturities',TEAL,'--',None),('Bills (short-term)',AMBER,':',None)],fontsize=17,ncol=2,y=.97)
    ax.axhline(50,color=REF,lw=1.1);ax.text(2008.1,45.0,'50% reference',fontsize=15,color=REF)
    ax.set_xlim(2007.7,2025.5);ax.set_ylim(0,100);ticks(ax,[0,25,50,75,100],'%');ax.set_xticks([2008,2013,2018,2025])
    save(fig,name)

if __name__=='__main__':
    premium_balance();estimates();fiscal_years();two_models();specification_curve();baseline_paths();ownership_levels();ownership_shares()
    for path,digest in hashes.items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
    provenance['checks']['all_source_hashes_unchanged']=True
    provenance['checks']['no_models_refitted']=True
    (OUT/'presentation-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(f'Rendered {len(provenance["charts"])} chart pairs; all numerical-source hashes unchanged.')

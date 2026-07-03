#!/usr/bin/env python3
import os,re,struct
import numpy as np

D=0.05; y_bed0=-0.025; alpha_thr=0.30; U_mean=0.3501

def read_scalar(fp):
    with open(fp,'r',errors='replace') as f: raw=f.read()
    m=re.search(r'internalField\s+nonuniform\s+List<scalar>\s*\n(\d+)\s*\n\(([^)]+)\)',raw,re.DOTALL)
    if m: return np.fromstring(m.group(2),sep='\n')
    m=re.search(r'internalField\s+uniform\s+([\S]+)',raw)
    if m: return np.array([float(m.group(1))])
    if 'format          binary' in raw or 'format binary' in raw:
        m2=re.search(r'internalField\s+nonuniform\s+List<scalar>\s*\n(\d+)',raw)
        if m2:
            n=int(m2.group(1))
            with open(fp,'rb') as fb: content=fb.read()
            start=content.rfind(b'(\n')
            if start!=-1: return np.array(struct.unpack_from(f'<{n}d',content,start+2))
    raise ValueError(f'Cannot parse {fp}')

cx_f=os.path.join('0','Cx'); cy_f=os.path.join('0','Cy')
if not os.path.exists(cy_f):
    raise FileNotFoundError('Run: postProcess -func writeCellCentres -time 0  first')
x_cc=read_scalar(cx_f); y_cc=read_scalar(cy_f)
print(f'Mesh: {len(y_cc)} cells  y=[{y_cc.min():.4f},{y_cc.max():.4f}]')
xm=(x_cc>=-D/2)&(x_cc<=D/2)
if xm.sum()==0: xm=np.ones(len(x_cc),dtype=bool)
print(f'Centreline cells: {xm.sum()}')

tds=sorted([(float(e),e) for e in os.listdir('.') if os.path.isdir(e) and os.path.exists(os.path.join(e,'alpha.a')) and e.replace('.','',1).isdigit()],key=lambda x:x[0])
print(f'Time dirs: {len(tds)}  ({tds[0][0]}->{tds[-1][0]} s)\n')

records=[]
for t,td in tds:
    try:
        al=read_scalar(os.path.join(td,'alpha.a'))
        if al.size==1: yb=y_bed0
        else:
            ac=al[xm] if al.size==len(y_cc) else al
            yc=y_cc[xm] if al.size==len(y_cc) else y_cc
            sm=ac>alpha_thr; yb=yc[sm].max() if sm.sum()>0 else y_bed0
        SD=max(0.0,(y_bed0-yb)/D); Ts=t*U_mean/D
        records.append((t,Ts,yb,SD))
        print(f't={t:5.1f}s T*={Ts:6.2f} y_bed={yb:+.5f}m S/D={SD:.4f}')
    except Exception as e: print(f'SKIP {td}: {e}')

with open('scour_St_D.csv','w') as f:
    f.write('t_s,T_star,y_bed_m,S_D\n')
    for r in records: f.write(f'{r[0]:.3f},{r[1]:.4f},{r[2]:.6f},{r[3]:.6f}\n')
print(f'\nSaved scour_St_D.csv ({len(records)} rows)')

lT=[0,1,3,5,8,12,20,40]; lS=[0,0.12,0.26,0.35,0.42,0.48,0.53,0.57]
mT=[0,2,5,10,20,50];      mS=[0,0.10,0.22,0.33,0.42,0.52]
sfT=[i*0.5 for i in range(121)]; Seq=0.580
sfS=[round(Seq*(1-2.718281828**(-x/5.0)),5) for x in sfT]
sT=[r[1] for r in records]; sS=[r[3] for r in records]

def interp(xs,ys,xi):
    if xi<=xs[0]: return ys[0]
    if xi>=xs[-1]: return ys[-1]
    for i in range(len(xs)-1):
        if xs[i]<=xi<=xs[i+1]:
            f=(xi-xs[i])/(xs[i+1]-xs[i]); return ys[i]+f*(ys[i+1]-ys[i])

rows_html=""
for t_check in [0,0.5,1.0,1.5,2.0,2.5,3.0,3.6,4.0,5.0]:
    if not records: continue
    r=min(records,key=lambda x:abs(x[0]-t_check))
    Ts=r[1]; sd=r[3]
    lv=interp(lT,lS,Ts); mv=interp(mT,mS,Ts)
    err=abs(sd-lv) if lv else 0
    bg="#d4edda" if err<0.05 else ("#fff3cd" if err<0.12 else "#f8d7da")
    st="GOOD" if err<0.05 else (f"±{err/max(lv,0.001):.0%}" if err<0.12 else "CHECK")
    rows_html+=f'<tr style="background:{bg}"><td>{r[0]:.1f}</td><td>{Ts:.1f}</td><td><b>{sd:.4f}</b></td><td>{lv:.3f}</td><td>{mv:.3f}</td><td>{st}</td></tr>\n'

Tmax=max(sT+[55.0]); lastT=sT[-1] if sT else 5.0; lastt=records[-1][0] if records else 5.0
html=f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Scour Validation</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script></head>
<body style="background:#fff;font-family:Arial,sans-serif;padding:24px;max-width:1100px">
<h2 style="color:#01696f">2DPipelineScour — S(t)/D Validation vs Literature</h2>
<p style="color:#666">θ=0.320 | D=0.05 m | d₅₀=0.36 mm | u*=0.04318 m/s | U=0.3501 m/s</p>
<div id="chart" style="width:100%;height:500px"></div>
<script>
Plotly.newPlot('chart',[
  {{x:{sfT},y:{sfS},mode:'lines',line:{{dash:'dash',color:'#bbb',width:1.5}},name:'Sumer-Fredsøe model (T_scale*=5)'}},
  {{x:{lT},y:{lS},mode:'lines+markers',line:{{color:'#da7101',width:2.5}},marker:{{size:8}},name:'Larsen et al. 2016 (CFD, θ≈0.30)'}},
  {{x:{mT},y:{mS},mode:'markers',marker:{{size:10,symbol:'square',color:'#a12c7b',line:{{color:'white',width:1.5}}}},name:'Mao 1986 (experiment)'}},
  {{x:{sT},y:{sS},mode:'lines+markers',line:{{color:'#01696f',width:3}},marker:{{size:5}},name:'SedFoam — this run'}}
],{{
  xaxis:{{title:'T* = t·U/D (dimensionless time)',gridcolor:'#eee',range:[0,{Tmax:.0f}]}},
  yaxis:{{title:'S(t)/D (scour depth ratio)',gridcolor:'#eee',range:[0,0.72]}},
  shapes:[
    {{type:'line',x0:0,x1:{Tmax:.0f},y0:{Seq},y1:{Seq},line:{{dash:'dot',color:'#a12c7b',width:1.2}}}},
    {{type:'line',x0:{lastT:.2f},x1:{lastT:.2f},y0:0,y1:0.68,line:{{dash:'dash',color:'#555',width:1.5}}}}
  ],
  annotations:[
    {{x:{Tmax*0.85:.1f},y:{Seq+0.025:.3f},text:'S_eq/D=0.58 (Mao 1986)',showarrow:false,font:{{size:11,color:'#a12c7b'}}}},
    {{x:{lastT+0.5:.1f},y:0.64,text:'sim end<br>t={lastt:.1f}s',showarrow:false,font:{{size:10,color:'#555'}}}}
  ],
  legend:{{orientation:'h',y:1.12,x:0.5,xanchor:'center'}},
  paper_bgcolor:'white',plot_bgcolor:'white'
}},{{responsive:true}});
</script>
<h3 style="margin-top:32px;color:#01696f">Validation Matrix</h3>
<table border="1" cellpadding="7" style="border-collapse:collapse;font-size:13px;width:100%">
<thead><tr style="background:#01696f;color:white;text-align:center">
<th>t (s)</th><th>T*</th><th>SedFoam S/D</th><th>Larsen 2016</th><th>Mao 1986</th><th>Status</th></tr></thead>
<tbody>{rows_html}</tbody></table>
<p style="color:#888;font-size:11px;margin-top:16px">
Mao (1986) Series Paper 39, ISVA DTU | Larsen et al. (2016) Coastal Engineering |
Sumer &amp; Fredsøe (2002) Mechanics of Scour in the Marine Environment</p>
</body></html>"""

with open('scour_validation.html','w') as f: f.write(html)
print('Saved scour_validation.html — open in Windows browser')
print('DONE')

"""설비별 평상 범위(평균 ± 2표준편차)로 이상 후보를 표시하고, 진동 그래프 한 장짜리 index.html을 만든다.
실행: 작업 폴더에서 python3 -I analyze.py  (data/Day5_설비센서_50건_가상.csv 를 읽는다)
"""
import csv, json, statistics as st
from pathlib import Path

CSV = Path("data/Day5_설비센서_50건_가상.csv")
rows = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))
eqs = {}
for r in rows:
    eqs.setdefault(r["설비"][:3], []).append(r)   # '설비A', '설비B' — 설비별로 따로 계산

def band(vals):
    m, s = st.mean(vals), st.stdev(vals)
    return m, s, m - 2 * s, m + 2 * s

res = {}
for name, rs in eqs.items():
    res[name] = {}
    for col in ("진동(mm/s)", "온도(℃)", "압력(bar)"):
        v = [float(x[col]) for x in rs]
        m, s, lo, hi = band(v)
        flags = [(rs[i]["시간"][-5:], v[i]) for i in range(len(v)) if v[i] < lo or v[i] > hi]
        res[name][col] = dict(mean=m, sd=s, lo=lo, hi=hi, flags=flags, values=v)

a, b = res["설비A"]["진동(mm/s)"], res["설비B"]["진동(mm/s)"]
bt = res["설비B"]["온도(℃)"]
times = [x["시간"][-5:] for x in eqs["설비A"]]

exp = {"values": {
    "a_vib_upper":  {"value": round(a["hi"], 1), "decimals": 1, "block": 1},
    "b_vib_upper":  {"value": round(b["hi"], 1), "decimals": 1, "block": 1},
    "a_flag_count": {"value": len(a["flags"]), "decimals": 0, "block": 1},
    "a_flag_value": {"value": a["flags"][0][1], "decimals": 1, "block": 1},
    "b_flag_count": {"value": len(b["flags"]), "decimals": 0, "block": 1},
    "b_flag_prev":  {"value": b["flags"][0][1], "decimals": 1, "block": 1},
    "b_flag_last":  {"value": b["flags"][1][1], "decimals": 1, "block": 1},
    "b_temp_flag":  {"value": bt["flags"][0][1], "decimals": 1, "block": 1},
}}
Path("expected.json").write_text(json.dumps(exp, ensure_ascii=False, indent=2), encoding="utf-8")

# ---- 그래프 한 장: 차트는 브라우저에서 그린다(글자 크기가 화면 폭에 따라 줄지 않게) ----
data = {
    "times": times, "a": a["values"], "b": b["values"],
    "aHi": round(a["hi"], 3), "bHi": round(b["hi"], 3),
    "aFlag": [t for t, _ in a["flags"]], "bFlag": [t for t, _ in b["flags"]],
}
tpl = r'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>노이즈 vs 추세</title>
<style>
:root{--bg:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--grid:#e4e3df;--ref:#52514e;--s1:#2a78d6;--s2:#eb6834;--tint:rgba(235,104,52,.10);--card:#f4f3f0}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--grid:#34332f;--ref:#c3c2b7;--s1:#3987e5;--s2:#d95926;--tint:rgba(217,89,38,.16);--card:#242422}}
:root[data-theme="dark"]{--bg:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--grid:#34332f;--ref:#c3c2b7;--s1:#3987e5;--s2:#d95926;--tint:rgba(217,89,38,.16);--card:#242422}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Malgun Gothic",sans-serif}
main{max-width:820px;margin:0 auto;padding:20px 16px 32px}
h1{font-size:clamp(22px,5vw,30px);line-height:1.25;margin:0 0 6px}
.sub{color:var(--ink2);margin:0 0 16px;font-size:15px}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px}
@media (max-width:560px){.cards{grid-template-columns:1fr}}
.card{background:var(--card);border-radius:10px;padding:12px 14px;border-left:6px solid}
.card.a{border-color:var(--s1)}.card.b{border-color:var(--s2)}
.card .tag{font-weight:700;font-size:15px}.card .big{font-size:20px;font-weight:700;margin:2px 0}.card .why{color:var(--ink2);font-size:14px}
.legend{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:14px;color:var(--ink2);margin-bottom:4px}
.legend span{display:inline-flex;align-items:center;gap:6px}
.legend svg{width:26px;height:12px}
#chart{position:relative;width:100%}
#chart svg{display:block;width:100%;touch-action:pan-y}
.tick{fill:var(--ink2);font-size:13px}.lab{fill:var(--ink);font-size:14px;font-weight:600}.note{fill:var(--ink2);font-size:13px}
#tip{position:absolute;pointer-events:none;background:var(--bg);color:var(--ink);border:1px solid var(--grid);border-radius:8px;padding:8px 10px;font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,.18);display:none;white-space:nowrap}
#tip b{display:block;margin-bottom:2px}
#tip i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
details{margin-top:16px;font-size:14px}summary{cursor:pointer;color:var(--ink2);padding:6px 0}
table{border-collapse:collapse;width:100%;margin-top:6px}th,td{padding:5px 8px;text-align:right;border-bottom:1px solid var(--grid)}th:first-child,td:first-child{text-align:left}
.src{color:var(--ink2);font-size:13px;margin-top:16px}
</style></head><body><main>
<h1>정비 신호는 설비 B — 한 번 튄 설비 A는 노이즈</h1>
<p class="sub">진동(mm/s), 20분 간격, 2026-09-15 08:00~16:00. 점선은 설비별 평균+2σ 상한(약 2.1)입니다.</p>
<div class="cards">
 <div class="card a"><div class="tag">● 설비 A · 노이즈</div><div class="big">12:40 한 번 __AV__</div><div class="why">곧바로 정상으로 돌아옴 → 한 점은 정비 신호가 아님</div></div>
 <div class="card b"><div class="tag">▲ 설비 B · 추세</div><div class="big">1.0 → 1.3 → 1.7 → 2.2 → __BV__</div><div class="why">꾸준히 오르는 흐름 → 정비 신호</div></div>
</div>
<div class="legend">
 <span><svg viewBox="0 0 26 12"><line x1="0" x2="26" y1="6" y2="6" stroke="var(--s1)" stroke-width="3"/></svg>설비 A 진동</span>
 <span><svg viewBox="0 0 26 12"><line x1="0" x2="26" y1="6" y2="6" stroke="var(--s2)" stroke-width="3"/></svg>설비 B 진동</span>
 <span><svg viewBox="0 0 26 12"><line x1="0" x2="26" y1="6" y2="6" stroke="var(--ref)" stroke-width="2" stroke-dasharray="5 4"/></svg>평균+2σ 상한</span>
 <span><svg viewBox="0 0 26 12"><circle cx="13" cy="6" r="5" fill="var(--ink2)"/></svg>이상 후보</span>
</div>
<div id="chart"><div id="tip"></div></div>
<details><summary>표로 보기</summary><div id="tbl"></div></details>
<p class="src">출처: keerhee/kma-auto-genai-3-1 · data/Day5/Day5_설비센서_50건_가상.csv · 가상 데이터(실제 설비 값 아님)</p>
</main>
<script>
const D=__DATA__;
const el=document.getElementById('chart'),tip=document.getElementById('tip');
const NS='http://www.w3.org/2000/svg';
function mk(t,at,txt){const e=document.createElementNS(NS,t);for(const k in at)e.setAttribute(k,at[k]);if(txt!=null)e.textContent=txt;return e}
function draw(){
 const old=el.querySelector('svg');if(old)old.remove();
 const w=el.clientWidth,narrow=w<520,h=narrow?340:400;
 const L=34,R=narrow?58:78,T=28,B=30,n=D.times.length,ymax=4;
 const X=i=>L+i*(w-L-R)/(n-1),Y=v=>T+(1-v/ymax)*(h-T-B);
 const s=mk('svg',{viewBox:`0 0 ${w} ${h}`,height:h,role:'img','aria-label':'설비 A·B 진동 추이'});
 for(const g of [0,1,2,3,4]){s.append(mk('line',{x1:L,x2:w-R,y1:Y(g),y2:Y(g),stroke:'var(--grid)'}));s.append(mk('text',{x:L-8,y:Y(g)+4,'text-anchor':'end',class:'tick'},g))}
 s.append(mk('text',{x:0,y:12,'text-anchor':'start',class:'tick'},'진동 mm/s'));
 for(let i=0;i<n;i+=(narrow?6:3)){s.append(mk('text',{x:X(i),y:h-8,'text-anchor':'middle',class:'tick'},D.times[i]))}
 const t0=D.times.indexOf('14:40');
 s.append(mk('rect',{x:X(t0),y:T,width:X(n-1)-X(t0),height:h-T-B,fill:'var(--tint)'}));
 s.append(mk('text',{x:X(t0)+6,y:T+16,class:'note'},'꾸준한 상승 구간'));
 for(const [hi,dx] of [[D.aHi,0],[D.bHi,0]]) s.append(mk('line',{x1:L,x2:w-R,y1:Y(hi),y2:Y(hi),stroke:'var(--ref)','stroke-width':1.5,'stroke-dasharray':'5 4'}));
 s.append(mk('text',{x:L+4,y:Y(D.aHi)-6,class:'note'},'상한 약 2.1'));
 const path=v=>v.map((y,i)=>(i?'L':'M')+X(i).toFixed(1)+','+Y(y).toFixed(1)).join(' ');
 s.append(mk('path',{d:path(D.a),fill:'none',stroke:'var(--s1)','stroke-width':2.5,'stroke-linejoin':'round'}));
 s.append(mk('path',{d:path(D.b),fill:'none',stroke:'var(--s2)','stroke-width':2.5,'stroke-linejoin':'round'}));
 const dot=(i,v,c)=>s.append(mk('circle',{cx:X(i),cy:Y(v),r:5.5,fill:c,stroke:'var(--bg)','stroke-width':2}));
 D.aFlag.forEach(t=>{const i=D.times.indexOf(t);dot(i,D.a[i],'var(--s1)');
   s.append(mk('text',{x:X(i)-10,y:Y(D.a[i])+5,'text-anchor':'end',class:'lab'},t+' · '+D.a[i].toFixed(1)));
   s.append(mk('text',{x:X(i)-10,y:Y(D.a[i])+22,'text-anchor':'end',class:'note'},'한 번 튀고 복귀'))});
 D.bFlag.forEach(t=>{const i=D.times.indexOf(t);dot(i,D.b[i],'var(--s2)')});
 s.append(mk('text',{x:w-R+8,y:Y(D.b[n-1])+5,class:'lab'},'B '+D.b[n-1].toFixed(1)));
 s.append(mk('text',{x:w-R+8,y:Y(D.a[n-1])+5,class:'lab'},'A '+D.a[n-1].toFixed(1)));
 const cross=mk('line',{y1:T,y2:h-B,stroke:'var(--ink2)','stroke-width':1,visibility:'hidden'});s.append(cross);
 const hit=mk('rect',{x:L,y:T,width:w-L-R,height:h-T-B,fill:'transparent'});s.append(hit);
 const move=e=>{const r=s.getBoundingClientRect(),px=(e.touches?e.touches[0].clientX:e.clientX)-r.left;
   const i=Math.max(0,Math.min(n-1,Math.round((px-L)/((w-L-R)/(n-1)))));
   cross.setAttribute('x1',X(i));cross.setAttribute('x2',X(i));cross.setAttribute('visibility','visible');
   const fa=D.aFlag.includes(D.times[i])?' · 이상 후보':'',fb=D.bFlag.includes(D.times[i])?' · 이상 후보':'';
   tip.innerHTML=`<b>${D.times[i]}</b><div><i style="background:var(--s1)"></i>설비 A ${D.a[i].toFixed(2)}${fa}</div><div><i style="background:var(--s2)"></i>설비 B ${D.b[i].toFixed(2)}${fb}</div>`;
   tip.style.display='block';const tw=tip.offsetWidth;let lx=X(i)+12;if(lx+tw>w)lx=X(i)-tw-12;tip.style.left=Math.max(0,lx)+'px';tip.style.top='8px'};
 const out=()=>{cross.setAttribute('visibility','hidden');tip.style.display='none'};
 hit.addEventListener('mousemove',move);hit.addEventListener('touchstart',move,{passive:true});hit.addEventListener('touchmove',move,{passive:true});hit.addEventListener('mouseleave',out);hit.addEventListener('touchend',out);
 el.append(s);
}
draw();new ResizeObserver(draw).observe(el);
document.getElementById('tbl').innerHTML='<table><tr><th>시간</th><th>설비 A</th><th>설비 B</th></tr>'+D.times.map((t,i)=>`<tr><td>${t}</td><td>${D.a[i].toFixed(2)}${D.aFlag.includes(t)?' ●':''}</td><td>${D.b[i].toFixed(2)}${D.bFlag.includes(t)?' ●':''}</td></tr>`).join('')+'</table><p class="src">● = 이상 후보(평균±2σ 밖)</p>';
</script></body></html>'''
html = (tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False))
           .replace("__AV__", f"{a['flags'][0][1]:.1f}").replace("__BV__", f"{b['values'][-1]:.1f}"))
Path("index.html").write_text(html, encoding="utf-8")
print(json.dumps({k: v["value"] for k, v in exp["values"].items()}, ensure_ascii=False))

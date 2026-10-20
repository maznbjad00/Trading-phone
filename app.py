import os, json, urllib.request, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE=r'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><title>الليل المالي</title><style>
*{box-sizing:border-box}body{margin:0;background:#07111f;color:#e9f1fc;font-family:system-ui,-apple-system,sans-serif}.top{padding:7px 12px 6px;background:#0b1829;z-index:5}h1{font-size:17px;margin:0}.sub{color:#8da1bd;font-size:12px;margin-top:5px}.tabs{display:flex;gap:6px;margin-top:7px}.tabs button,.actions button{background:#1a2c42;color:#dde9fb;border:1px solid #314862;padding:7px;border-radius:9px;flex:1;font-weight:bold}.tabs .active{background:#184f6a;border-color:#3289ac}.main{padding:5px 9px}.row{background:#102239;border:1px solid #29425e;padding:7px;margin:4px 0;border-radius:9px;display:flex;justify-content:space-between;align-items:center}.sym{font-size:16px;font-weight:800}.light{color:#9db2c9;font-size:12px}.green{color:#5be4a5}.charts{display:block}.chart{height:clamp(185px,34dvh,285px);background:#0d1d30;border-radius:9px;margin-bottom:3px;overflow:hidden}.chart.flow{height:clamp(125px,22dvh,185px)}.title{font-size:11px;color:#a7bbd2;margin:4px 1px 3px}.notice{padding:12px;border:1px solid #614b32;background:#322619;border-radius:12px;color:#f4cc94;font-size:12px;line-height:1.8}.actions{display:flex;gap:8px;direction:ltr}input{width:100%;background:#162a40;color:white;border:1px solid #415e7b;padding:13px;border-radius:10px;margin:8px 0 12px;font-size:16px}.error{font-size:12px;color:#ffafa6}.footer{display:none}</style></head><body>
<div class="top"><h1>الليل المالي <span style="color:#59d6ae">◉</span></h1><div class="tabs"><button id="tab-list" onclick="page('list')">الرصد</button><button class="active" id="tab-charts" onclick="page('charts')">الشارت والسيولة</button></div></div>
<div class="main"><section id="list" style="display:none"><div class="notice">هذه نسخة معاينة آمنة؛ لن تعرض إشارات اختراق أو FIRE دون وصول فعلي لبيانات الصفقات. لا توجد أرقام سوق مفبركة.</div><label class="title">رمز السهم</label><input id="search" placeholder="مثال: AAPL" autocapitalize="characters" value="AAPL"><div class="actions"><button onclick="openSymbol()">افتح الشارت</button></div><div id="state" class="light" style="margin-top:15px"></div></section>
<section class="charts" id="charts"><div class="row"><div><div class="sym" id="symbol">AAPL</div><div class="light">السعر — شموع الدقيقة</div></div><button onclick="page('list')" style="background:#20334b;border:0;color:white;padding:10px;border-radius:8px">رجوع</button></div><div class="title">شموع دقيقة — TradingView Lightweight Charts</div><div id="candles" class="chart"></div><div class="title">صافي السيولة بالدقيقة</div><div id="flow" class="chart flow"></div><div class="notice" id="msg" style="padding:5px;font-size:10px;line-height:1.35">صافي السيولة يحتاج صفقات منفذة وبيانات اتجاه التداول؛ لا يُستنتج من شموع OHLC وحدها.</div></section></div><div class="footer">الليل المالي — قراءة وتحليل فقط، لا ينفذ أوامر تداول</div>
<script src="https://unpkg.com/lightweight-charts@4.2.3/dist/lightweight-charts.standalone.production.js"></script><script>
let c,f;let syncLock=false;let refreshTimer=null;
function syncCharts(a,b){const x=a.timeScale(),y=b.timeScale();x.subscribeVisibleTimeRangeChange(r=>{if(syncLock||!r)return;syncLock=true;try{y.setVisibleRange(r)}catch(e){}syncLock=false});y.subscribeVisibleTimeRangeChange(r=>{if(syncLock||!r)return;syncLock=true;try{x.setVisibleRange(r)}catch(e){}syncLock=false})}
function page(n){document.getElementById('list').style.display=n==='list'?'block':'none';document.getElementById('charts').style.display=n==='charts'?'block':'none';document.getElementById('tab-list').classList.toggle('active',n==='list');document.getElementById('tab-charts').classList.toggle('active',n==='charts');if(n==='charts'&&c){setTimeout(()=>{c.applyOptions({width:document.getElementById('candles').clientWidth});f.applyOptions({width:document.getElementById('flow').clientWidth})},80)}}
function chart(id,h){let el=document.getElementById(id);return LightweightCharts.createChart(el,{width:el.clientWidth,height:h,layout:{background:{color:'#0d1d30'},textColor:'#a7bed9'},grid:{vertLines:{color:'#182b42'},horzLines:{color:'#182b42'}},rightPriceScale:{borderColor:'#304860'},timeScale:{borderColor:'#304860',timeVisible:true,secondsVisible:false}})}
async function openSymbol(){let s=document.getElementById('search').value.trim().toUpperCase().replace(/[^A-Z.]/g,'');if(!s)return;document.getElementById('symbol').textContent=s;page('charts');if(refreshTimer)clearInterval(refreshTimer);document.getElementById('candles').innerHTML='';document.getElementById('flow').innerHTML='';c=chart('candles',document.getElementById('candles').clientHeight);f=chart('flow',document.getElementById('flow').clientHeight);let series=c.addCandlestickSeries({upColor:'#0d1d30',downColor:'#ef607b',borderUpColor:'#55deb0',borderDownColor:'#ef607b',wickUpColor:'#55deb0',wickDownColor:'#ef607b'});let flow=f.addLineSeries({color:'#55baf4',lineWidth:2});syncCharts(c,f);try{let r=await fetch('/api/bars?symbol='+encodeURIComponent(s));let j=await r.json();if(!r.ok){let details=Object.entries(j.details||{}).map(([feed,msg])=>feed.toUpperCase()+': '+msg).join(' | ');throw Error((j.error||'تعذر تحميل البيانات')+(details?' — '+details:'')+' (HTTP '+r.status+')')};series.setData(j.bars);c.timeScale().fitContent();let statuses=Object.entries(j.feeds||{}).map(([k,v])=>k.toUpperCase()+': '+(v.ok?'متاح ('+v.count+')':'غير متاح')).join(' | ');document.getElementById('msg').textContent=statuses+' — جاري حساب السيولة من الصفقات...';try{let lr=await fetch('/api/liquidity?symbol='+encodeURIComponent(s));let lj=await lr.json();if(!lr.ok)throw Error(lj.error+' '+JSON.stringify(lj.feeds||{}));flow.setData(lj.points);const currentSession=lj.active_session==='night'?'الليلي (20:00–04:00)':'اليومي (04:00–20:00)';document.getElementById('msg').textContent='صافي السيولة التقديري — '+currentSession+'، يبدأ من الصفر عند بداية الجلسة — '+(lj.partial?'العينة جزئية؛ بعض الصفقات لم تحمّل':'')+' | '+Object.entries(lj.feeds||{}).map(([k,v])=>k.toUpperCase()+': '+(v.ok?v.trades+' صفقة':'غير متاح')).join(' | ')}catch(liqerr){document.getElementById('msg').textContent='الشموع متاحة؛ السيولة غير متاحة: '+liqerr.message};}catch(e){document.getElementById('msg').textContent=e.message}
if(refreshTimer)clearInterval(refreshTimer);
refreshTimer=setInterval(async()=>{
 if(document.hidden||document.getElementById('charts').style.display==='none')return;
 try{
  let r=await fetch('/api/liquidity?symbol='+encodeURIComponent(s),{cache:'no-store'});
  let j=await r.json();
  if(!r.ok||!Array.isArray(j.points)||!j.points.length)return;
  flow.setData(j.points);
  document.getElementById('msg').textContent='السيولة تتحدث كل دقيقتين — '+(j.active_session==='night'?'جلسة الليلي':'جلسة اليوم')+(j.partial?' (بيانات جزئية)':'');
 }catch(e){console.debug('Liquidity refresh failed',e)}
},120000);
}
window.addEventListener('load',()=>openSymbol());</script></body></html>'''

def get_liquidity(symbol,key,sec):
 from datetime import datetime,timedelta,timezone
 from zoneinfo import ZoneInfo
 now=datetime.now(timezone.utc)
 ny=now.astimezone(ZoneInfo('America/New_York'))
 night=ny.hour>=20 or ny.hour<4
 if night:
  session_start=ny.replace(hour=20,minute=0,second=0,microsecond=0)
  if ny.hour<4:session_start-=timedelta(days=1)
  session_end=session_start+timedelta(hours=8)
  feed='boats'
 else:
  session_start=ny.replace(hour=4,minute=0,second=0,microsecond=0)
  session_end=session_start+timedelta(hours=16)
  feed='sip'
 start=session_start.astimezone(timezone.utc)
 end=min(now,session_end.astimezone(timezone.utc))
 stamp=lambda d:d.isoformat().replace('+00:00','Z')
 headers={'APCA-API-KEY-ID':key,'APCA-API-SECRET-KEY':sec}
 buckets={};token=None;count=0;direction=0;last_price=None;partial=False
 try:
  for page in range(20):
   params={'symbols':symbol,'start':stamp(start),'end':stamp(end),'limit':10000,'feed':feed,'sort':'asc'}
   if token:params['page_token']=token
   req=urllib.request.Request('https://data.alpaca.markets/v2/stocks/trades?'+urllib.parse.urlencode(params),headers=headers)
   with urllib.request.urlopen(req,timeout=20) as resp:data=json.load(resp)
   for trade in data.get('trades',{}).get(symbol,[]):
    price=float(trade['p']);size=float(trade['s'])
    if last_price is not None:
     if price>last_price:direction=1
     elif price<last_price:direction=-1
    last_price=price
    if direction:
     minute=int(datetime.fromisoformat(trade['t'].replace('Z','+00:00')).timestamp())//60*60
     buckets[minute]=buckets.get(minute,0.0)+direction*price*size
    count+=1
   token=data.get('next_page_token')
   if not token:break
  partial=bool(token)
 except urllib.error.HTTPError as exc:
  return {'points':[],'feeds':{feed:{'ok':False,'error':'HTTP '+str(exc.code)}},'active_session':'night' if night else 'day','partial':True}
 except Exception:
  return {'points':[],'feeds':{feed:{'ok':False,'error':'تعذر طلب الصفقات'}},'active_session':'night' if night else 'day','partial':True}
 cumulative=0.0;points=[]
 for t,v in sorted(buckets.items()):
  cumulative+=v
  points.append({'time':t,'value':round(cumulative,2)})
 return {'points':points,'feeds':{feed:{'ok':True,'trades':count,'partial':partial}},'active_session':'night' if night else 'day','session_start':stamp(start),'partial':partial,'method':'tick rule signed notional approximation'}

class Handler(BaseHTTPRequestHandler):
 def out(self,code,data,typ='application/json; charset=utf-8'):
  raw=data.encode() if isinstance(data,str) else json.dumps(data).encode()
  self.send_response(code);self.send_header('Content-Type',typ);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  if self.path.startswith('/health'):return self.out(200,{'ok':True})
  if self.path=='/':return self.out(200,PAGE,'text/html; charset=utf-8')
  path=urllib.parse.urlsplit(self.path)
  if path.path=='/api/liquidity':
   q=urllib.parse.parse_qs(path.query);symbol=q.get('symbol',[''])[0].upper()
   if not symbol or len(symbol)>12 or not all(c.isalpha() or c=='.' for c in symbol):return self.out(400,{'error':'رمز غير صالح'})
   key=os.getenv('ALPACA_API_KEY','');sec=os.getenv('ALPACA_SECRET_KEY','')
   if not key or not sec:return self.out(503,{'error':'مفاتيح Alpaca غير مضافة'})
   result=get_liquidity(symbol,key,sec)
   if not result['points']:return self.out(422,{'error':'لم تتوفر صفقات كافية لحساب تدفق السيولة','feeds':result['feeds']})
   return self.out(200,result)
  if path.path=='/api/bars':
   q=urllib.parse.parse_qs(path.query);s=q.get('symbol',[''])[0].upper()
   if not s or len(s)>12 or not all(c.isalpha() or c=='.' for c in s):return self.out(400,{'error':'رمز سهم غير صالح'})
   key=os.getenv('ALPACA_API_KEY','');sec=os.getenv('ALPACA_SECRET_KEY','')
   if not key or not sec:return self.out(503,{'error':'أضف مفاتيح Alpaca إلى Railway Variables لعرض الشموع الحقيقية'})
   from datetime import datetime,timedelta,timezone
   end=datetime.now(timezone.utc);start=end-timedelta(days=3)
   stamp=lambda d:d.isoformat().replace('+00:00','Z')
   headers={'APCA-API-KEY-ID':key,'APCA-API-SECRET-KEY':sec}
   merged={};sources={};errors={}
   for feed in ('sip','boats'):
    try:
     token=None;count=0;total=0
     while count<5:
      params={'symbols':s,'timeframe':'1Min','start':stamp(start),'end':stamp(end),'limit':10000,'feed':feed,'sort':'asc'}
      if token:params['page_token']=token
      req=urllib.request.Request('https://data.alpaca.markets/v2/stocks/bars?'+urllib.parse.urlencode(params),headers=headers)
      with urllib.request.urlopen(req,timeout=15) as res:d=json.load(res)
      for x in d.get('bars',{}).get(s,[]):
       t=int(datetime.fromisoformat(x['t'].replace('Z','+00:00')).timestamp())
       if feed=='boats' or t not in merged:
        merged[t]={'time':t,'open':x['o'],'high':x['h'],'low':x['l'],'close':x['c'],'feed':feed}
       total+=1
      token=d.get('next_page_token');count+=1
      if not token:break
     sources[feed]={'ok':True,'count':total,'partial':bool(token)}
    except urllib.error.HTTPError as exc:
     errors[feed]='HTTP '+str(exc.code)+' — راجع صلاحية بيانات '+feed.upper()
     sources[feed]={'ok':False,'count':0}
    except Exception:
     errors[feed]='تعذر جلب بيانات '+feed.upper()
     sources[feed]={'ok':False,'count':0}
   if not merged:return self.out(502,{'error':'تعذر الوصول لبيانات SIP وBOATS؛ تحقق من المفاتيح وصلاحيات الاشتراك','feeds':sources,'details':errors})
   bars=sorted(merged.values(),key=lambda x:x['time'])
   return self.out(200,{'bars':bars,'feeds':sources,'details':errors,'coverage':'SIP including extended sessions + BOATS overnight where available','live':False})
  return self.out(404,{'error':'Not found'})
if __name__=='__main__':ThreadingHTTPServer(('0.0.0.0',int(os.getenv('PORT','8080'))),Handler).serve_forever()

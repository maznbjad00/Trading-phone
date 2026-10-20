import os, json, base64, hmac, urllib.request, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE=r'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><title>الليل المالي</title><style>
*{box-sizing:border-box}body{margin:0;background:#07111f;color:#e9f1fc;font-family:system-ui,-apple-system,sans-serif}.top{padding:18px 14px 12px;position:sticky;top:0;background:#0b1829;z-index:5}h1{font-size:21px;margin:0}.sub{color:#8da1bd;font-size:12px;margin-top:5px}.tabs{display:flex;gap:8px;margin-top:16px}.tabs button,.actions button{background:#1a2c42;color:#dde9fb;border:1px solid #314862;padding:11px;border-radius:10px;flex:1;font-weight:bold}.tabs .active{background:#184f6a;border-color:#3289ac}.main{padding:12px}.row{background:#102239;border:1px solid #29425e;padding:12px;margin:8px 0;border-radius:12px;display:flex;justify-content:space-between;align-items:center}.sym{font-size:19px;font-weight:800}.light{color:#9db2c9;font-size:12px}.green{color:#5be4a5}.charts{display:none}.chart{height:280px;background:#0d1d30;border-radius:12px;margin-bottom:9px;overflow:hidden}.chart.flow{height:185px}.title{font-size:13px;color:#a7bbd2;margin:13px 1px 8px}.notice{padding:12px;border:1px solid #614b32;background:#322619;border-radius:12px;color:#f4cc94;font-size:12px;line-height:1.8}.actions{display:flex;gap:8px;direction:ltr}input{width:100%;background:#162a40;color:white;border:1px solid #415e7b;padding:13px;border-radius:10px;margin:8px 0 12px;font-size:16px}.error{font-size:12px;color:#ffafa6}.footer{color:#6f879f;font-size:11px;text-align:center;padding:20px}</style></head><body>
<div class="top"><h1>الليل المالي <span style="color:#59d6ae">◉</span></h1><div class="sub">شارت دقيقة + سيولة بالدقيقة — واجهة آيفون</div><div class="tabs"><button class="active" id="tab-list" onclick="page('list')">الرصد</button><button id="tab-charts" onclick="page('charts')">الشارت والسيولة</button></div></div>
<div class="main"><section id="list"><div class="notice">هذه نسخة معاينة آمنة؛ لن تعرض إشارات اختراق أو FIRE دون وصول فعلي لبيانات الصفقات. لا توجد أرقام سوق مفبركة.</div><label class="title">رمز السهم</label><input id="search" placeholder="مثال: AAPL" autocapitalize="characters" value="AAPL"><div class="actions"><button onclick="openSymbol()">افتح الشارت</button></div><div id="state" class="light" style="margin-top:15px"></div></section>
<section class="charts" id="charts"><div class="row"><div><div class="sym" id="symbol">AAPL</div><div class="light">السعر — شموع الدقيقة</div></div><button onclick="page('list')" style="background:#20334b;border:0;color:white;padding:10px;border-radius:8px">رجوع</button></div><div class="title">شموع دقيقة — TradingView Lightweight Charts</div><div id="candles" class="chart"></div><div class="title">صافي السيولة بالدقيقة</div><div id="flow" class="chart flow"></div><div class="notice" id="msg">صافي السيولة يحتاج صفقات منفذة وبيانات اتجاه التداول؛ لا يُستنتج من شموع OHLC وحدها.</div></section></div><div class="footer">الليل المالي — قراءة وتحليل فقط، لا ينفذ أوامر تداول</div>
<script src="https://unpkg.com/lightweight-charts@4.2.3/dist/lightweight-charts.standalone.production.js"></script><script>
let c,f;function page(n){document.getElementById('list').style.display=n==='list'?'block':'none';document.getElementById('charts').style.display=n==='charts'?'block':'none';document.getElementById('tab-list').classList.toggle('active',n==='list');document.getElementById('tab-charts').classList.toggle('active',n==='charts');if(n==='charts'&&c){setTimeout(()=>{c.applyOptions({width:document.getElementById('candles').clientWidth});f.applyOptions({width:document.getElementById('flow').clientWidth})},80)}}
function chart(id,h){let el=document.getElementById(id);return LightweightCharts.createChart(el,{width:el.clientWidth,height:h,layout:{background:{color:'#0d1d30'},textColor:'#a7bed9'},grid:{vertLines:{color:'#182b42'},horzLines:{color:'#182b42'}},rightPriceScale:{borderColor:'#304860'},timeScale:{borderColor:'#304860',timeVisible:true,secondsVisible:false}})}
async function openSymbol(){let s=document.getElementById('search').value.trim().toUpperCase().replace(/[^A-Z.]/g,'');if(!s)return;document.getElementById('symbol').textContent=s;page('charts');document.getElementById('candles').innerHTML='';document.getElementById('flow').innerHTML='';c=chart('candles',280);f=chart('flow',185);let series=c.addCandlestickSeries({upColor:'#0d1d30',downColor:'#ef607b',borderUpColor:'#55deb0',borderDownColor:'#ef607b',wickUpColor:'#55deb0',wickDownColor:'#ef607b'});let flow=f.addLineSeries({color:'#55baf4',lineWidth:2});try{let r=await fetch('/api/bars?symbol='+encodeURIComponent(s));let j=await r.json();if(!r.ok)throw Error(j.error||'تعذر تحميل البيانات');series.setData(j.bars);c.timeScale().fitContent();document.getElementById('msg').textContent='شموع سوق حقيقية عند توفر ترخيص Alpaca. خط السيولة سيظهر فقط عند ربط تيار الصفقات، دون تقدير مزيف من حجم الشموع.';}catch(e){document.getElementById('msg').textContent=e.message}}
</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
 def out(self,code,data,typ='application/json; charset=utf-8'):
  raw=data.encode() if isinstance(data,str) else json.dumps(data).encode()
  self.send_response(code);self.send_header('Content-Type',typ);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def auth(self):
  pwd=os.getenv('APP_PASSWORD','')
  if not pwd or len(pwd)<12:return False
  head=self.headers.get('Authorization','')
  try:
   method,token=head.split(' ',1)
   decoded=base64.b64decode(token).decode('utf-8')
   return method.lower()=='basic' and hmac.compare_digest(decoded,'layl:'+pwd)
  except Exception:return False
 def do_GET(self):
  if self.path.startswith('/health'):return self.out(200,{'ok':True})
  if not self.auth():
   self.send_response(401);self.send_header('WWW-Authenticate','Basic realm="Layl private"');self.end_headers();return
  if self.path=='/':return self.out(200,PAGE,'text/html; charset=utf-8')
  path=urllib.parse.urlsplit(self.path)
  if path.path=='/api/bars':
   q=urllib.parse.parse_qs(path.query);s=q.get('symbol',[''])[0].upper()
   if not s or len(s)>12 or not all(c.isalpha() or c=='.' for c in s):return self.out(400,{'error':'رمز سهم غير صالح'})
   key=os.getenv('ALPACA_API_KEY','');sec=os.getenv('ALPACA_SECRET_KEY','')
   if not key or not sec:return self.out(503,{'error':'أضف مفاتيح Alpaca إلى Railway Variables لعرض الشموع الحقيقية'})
   try:
    from datetime import datetime,timedelta,timezone
    end=datetime.now(timezone.utc);start=end-timedelta(days=4)
    params=urllib.parse.urlencode({'symbols':s,'timeframe':'1Min','start':start.isoformat().replace('+00:00','Z'),'end':end.isoformat().replace('+00:00','Z'),'limit':1000,'feed':'sip'})
    req=urllib.request.Request('https://data.alpaca.markets/v2/stocks/bars?'+params,headers={'APCA-API-KEY-ID':key,'APCA-API-SECRET-KEY':sec})
    with urllib.request.urlopen(req,timeout=12) as res:d=json.load(res)
    bars=[{'time':int(datetime.fromisoformat(x['t'].replace('Z','+00:00')).timestamp()),'open':x['o'],'high':x['h'],'low':x['l'],'close':x['c']} for x in d.get('bars',{}).get(s,[])]
    return self.out(200,{'bars':bars})
   except Exception as e:return self.out(502,{'error':'تعذر جلب شموع Alpaca؛ تحقق من اشتراك SIP والمفاتيح'})
  return self.out(404,{'error':'Not found'})
if __name__=='__main__':ThreadingHTTPServer(('0.0.0.0',int(os.getenv('PORT','8080'))),Handler).serve_forever()

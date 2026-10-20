"""Read-only automatic Alpaca whole-market streaming scanner.
Requires market data subscription supporting wildcard streams. In-memory state resets per ET session.
Historical liquidity gates are NOT emitted until historical 15m flow benchmarks are available.
"""
import os, json, time, threading
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from collections import deque
try:
 import websocket
except ImportError:
 websocket=None

NY=ZoneInfo("America/New_York")
class Scanner:
 def __init__(self):
  self.lock=threading.RLock()
  self.records={}
  self.status="starting"
  self.feed=None
  self.session=None
  self.connected=False
  self.updated=0
  self.last_error=""
  self.ws=None
  self.running=False
  self.thread=None
  self.generation=0
 def get_session(self):
  n=datetime.now(NY);h=n.hour
  feed="boats" if h>=20 or h<4 else "sip"
  name="night" if feed=="boats" else "day"
  anchor=n.replace(hour=20 if feed=="boats" else 4,minute=0,second=0,microsecond=0)
  if feed=="boats" and h<4:anchor-=timedelta(days=1)
  return feed,name,anchor.isoformat()
 def begin(self):
  if self.running:return
  if not os.getenv("ALPACA_API_KEY") or not os.getenv("ALPACA_SECRET_KEY"):
   self.status="missing Alpaca credentials";return
  if websocket is None:self.status="websocket-client missing";return
  self.running=True
  self.thread=threading.Thread(target=self.loop,daemon=True)
  self.thread.start()
 def event(self,m,feed):
  sym=m.get("S");kind=m.get("T")
  if kind not in ("t","b") or not sym or not sym.replace(".","").isalpha():return
  try:
   price=float(m.get("p") or m.get("c") or 0)
   if price<=0:return
   size=float(m.get("s") or 0)
   ts=datetime.fromisoformat(m["t"].replace("Z","+00:00")).timestamp()
  except (ValueError,TypeError,KeyError):return
  with self.lock:
   rec=self.records.get(sym)
   if rec is None:
    rec={"symbol":sym,"price":0,"high":price,"low":price,"flow":0,"net5":0,"last":0,"last_ts":0,
         "ticks":deque(),"flow5":deque(),"fire_at":0,"fire_count":0,"last_fire":None,
         "fire":False,"gate":"history_not_loaded","count":0}
    self.records[sym]=rec
   rec["price"]=price
   rec["high"]=max(rec["high"],price)
   rec["low"]=min(rec["low"],price)
   rec["last_ts"]=ts
   if kind!="t":return
   signed=(1 if price>rec["last"] else -1 if price<rec["last"] else 0)*price*size if rec["last"]>0 else 0
   rec["last"]=price;rec["flow"]+=signed;rec["count"]+=1
   q=rec["flow5"];q.append((ts,signed))
   while q and q[0][0]<=ts-300:q.popleft()
   rec["net5"]=round(sum(v for _,v in q),2)
   z=rec["ticks"];z.append((ts,price,size))
   while z and z[0][0]<=ts-65:z.popleft()
   last5=[(p,s) for t,p,s in z if t>ts-5]
   prev60=[(p,s) for t,p,s in z if ts-65<t<=ts-5]
   dollar5=sum(p*s for p,s in last5)
   base=sum(p*s for p,s in prev60)/12.0
   ratio=dollar5/base if base else 0
   prices=[p for p,_ in last5]
   span=(max(prices)-min(prices))/min(prices)*100 if len(prices)>1 and min(prices)>0 else 0
   trigger=(dollar5>=10000 and 2.5<=ratio<=100 and span>=0.3 and len(prev60)>0 and ts-rec["fire_at"]>=300)
   if trigger:
    rec["fire_at"]=ts;rec["fire_count"]+=1
    rec["last_fire"]={"time":ts,"dollar5":round(dollar5,2),"burst":round(ratio,2),"range_pct":round(span,2)}
   rec["fire"]=bool(rec["fire_at"] and ts-rec["fire_at"]<20)
   self.updated=time.time()
 def loop(self):
  while self.running:
   feed,session,anchor=self.get_session()
   with self.lock:
    if self.session!=anchor:
     self.records.clear()
     self.session=anchor
    self.feed=feed;self.connected=False;self.status="connecting "+feed
   url="wss://stream.data.alpaca.markets/"+("v1beta1/boats" if feed=="boats" else "v2/sip")
   def on_open(ws):
    ws.send(json.dumps({"action":"auth","key":os.getenv("ALPACA_API_KEY"),"secret":os.getenv("ALPACA_SECRET_KEY")}))
   def on_message(ws,raw):
    try:msgs=json.loads(raw)
    except Exception:return
    if isinstance(msgs,dict):msgs=[msgs]
    for m in msgs:
     kind=m.get("T")
     if kind=="success" and m.get("msg")=="authenticated":
      ws.send(json.dumps({"action":"subscribe","trades":["*"],"bars":["*"]}))
     elif kind=="subscription":
      self.connected=True;self.status="streaming "+feed
     elif kind=="error":
      self.connected=False;self.last_error=str(m.get("code"))+": "+str(m.get("msg"))
      self.status="Alpaca error";ws.close()
     elif kind in ("t","b"):self.event(m,feed)
   def on_error(ws,e):self.connected=False;self.last_error=str(e)[:180];self.status="connection error"
   self.ws=websocket.WebSocketApp(url,on_open=on_open,on_message=on_message,on_error=on_error,
                                   on_close=lambda *args:setattr(self,"connected",False))
   def boundary(ws):
    while self.running and self.ws is ws:
     if self.get_session()[2]!=anchor:ws.close();break
     time.sleep(3)
   threading.Thread(target=boundary,args=(self.ws,),daemon=True).start()
   try:self.ws.run_forever(ping_interval=20,ping_timeout=10)
   except Exception as e:self.last_error=str(e)[:180];self.status="stream error"
   time.sleep(5)
 def snapshot(self,limit=100):
  with self.lock:
   rows=[]
   for r in self.records.values():
    if r["count"]==0:continue
    rows.append({k:r[k] for k in ("symbol","price","high","low","flow","net5","last_ts","fire","fire_count","last_fire","gate")})
   rows.sort(key=lambda x:(bool(x["fire"]),x["net5"]),reverse=True)
   return {"status":self.status,"connected":self.connected,"feed":self.feed,
           "session_start":self.session,"symbol_count":len(self.records),"updated":self.updated,
           "last_error":self.last_error,"gate_status":"historical_15m_not_loaded",
           "rows":rows[:max(1,min(limit,250))]}
scanner=Scanner()

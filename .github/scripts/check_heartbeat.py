import os,sys,time,json,redis,datetime as dt
r=redis.from_url(os.environ['REDIS_URL']); now=time.time()
active={ w.decode().split(':')[-1] for w in r.smembers('rq:workers') }  # 目前存活 worker_id 集合
stale=[]; purged=[]
for k in r.scan_iter('worker:heartbeat:*'):
    key=k.decode(); val=(r.get(k) or b'{}').decode()
    try:
        m=json.loads(val); ts=m.get('last_heartbeat') or m.get('lastHeartbeat')
        t=dt.datetime.fromisoformat(str(ts).replace('Z','+00:00')).timestamp()
    except Exception: t=0
    age=int(now-t) if t else 999999
    wid=key.split(':')[-1]
    if wid not in active:
        if age>600: r.delete(k); purged.append(key)   # 清理孤兒鍵（>10m）
        continue                                      # 不納入判斷
    if age>120: stale.append((key,age))
if stale:
    print("Stale active heartbeats:", stale); sys.exit(1)
print("OK: active heartbeats fresh;", "purged_orphans="+str(len(purged)))

import os,sys,time,json,redis,datetime as dt
r=redis.from_url(os.environ['REDIS_URL']); now=time.time(); stale=[]
for k in r.scan_iter('worker:heartbeat:*'):
    v=(r.get(k) or b'{}').decode()
    try:
        ts=dt.datetime.fromisoformat(json.loads(v)['last_heartbeat'].replace('Z','')).timestamp()
        age=int(now-ts)
        if age>120: stale.append((k.decode(), age))
    except Exception: stale.append((k.decode(),'bad_payload'))
if stale: print("STALE:", stale); sys.exit(1)
print("OK: all heartbeats fresh"); sys.exit(0)

import os
import sys
import time
import json
import redis
import datetime as dt

r = redis.from_url(os.environ['REDIS_URL'])
now = time.time()
# 目前存活 worker_id 集合
active = {w.decode().split(':')[-1] for w in r.smembers('rq:workers')}
stale = []
purged = []
corrupted_cleanup = []

for k in r.scan_iter('worker:heartbeat:*'):
    key = k.decode()
    val = (r.get(k) or b'{}').decode()
    try:
        m = json.loads(val)
        ts = m.get('last_heartbeat') or m.get('lastHeartbeat')
        t = dt.datetime.fromisoformat(
            str(ts).replace('Z', '+00:00')
        ).timestamp()
    except Exception:
        t = 0
    age = int(now - t) if t else 999999
    wid = key.split(':')[-1]

    # Force-cleanup corrupted workers
    # (age=999999 = unparseable heartbeat)
    if age >= 999999:
        r.delete(k)
        r.srem('rq:workers', wid)
        corrupted_cleanup.append((key, wid))
        continue

    if wid not in active:
        # 清理孤兒鍵（>10m）
        if age > 600:
            r.delete(k)
            purged.append(key)
        continue
    if age > 120:
        stale.append((key, age))

if stale:
    print("Stale active heartbeats:", stale)
    sys.exit(1)

print(
    f"OK: active heartbeats fresh; "
    f"purged_orphans={len(purged)}; "
    f"corrupted_cleanup={len(corrupted_cleanup)}"
)

if corrupted_cleanup:
    print(f"Cleaned up corrupted workers: {corrupted_cleanup}")

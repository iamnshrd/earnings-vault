"""Сжимает kalshi_raw\\*.json в компактный kalshi_dataset.json: по каждому страйку цены до колла.
t0 = начало часа с максимальным суммарным объёмом по событию (старт колла). Снимки: за 1/6/24 ч до t0.
Запуск:  .venv\\Scripts\\python build_dataset.py
"""
import json, glob, os, bisect, collections, datetime as dt

def f(x):
    try: return float(x)
    except Exception: return None

def iso(s):
    return int(dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())

def g(d, k):
    return d.get(k + "_dollars", d.get(k))

def vv(c):
    return f(c.get("volume_fp", c.get("volume"))) or 0

def snap(cs, ts, t):
    """состояние на момент t по последней свече с end<=t"""
    i = bisect.bisect_right(ts, t) - 1
    if i < 0: return None, None, None
    c = cs[i]
    b, a = f(g(c["yes_bid"], "close")), f(g(c["yes_ask"], "close"))
    last = None
    for j in range(i, -1, -1):
        p = f(g(cs[j].get("price", {}), "close"))
        if p is not None: last = p; break
    return b, a, last

rows = []
for fn in sorted(glob.glob("kalshi_raw/*.json")):
    s = os.path.basename(fn)[:-5]
    d = json.load(open(fn))
    if not d.get("markets"): continue
    byev = collections.defaultdict(list)
    for m in d["markets"]: byev[m["event_ticker"]].append(m)
    for et, ms in byev.items():
        vol = collections.Counter()
        for m in ms:
            for c in d["candles"].get(m["ticker"], []):
                vol[c["end_period_ts"]] += vv(c)
        if not vol: continue
        tpk = max(vol, key=vol.get)
        t0 = tpk - 3600
        tot = sum(vol.values())
        for m in ms:
            cs = d["candles"].get(m["ticker"], [])
            ts = [c["end_period_ts"] for c in cs]
            r = {"series": s, "event": et, "ticker": m["ticker"],
                 "word": (m.get("custom_strike") or {}).get("Word") or m.get("yes_sub_title"),
                 "result": m.get("result"), "created": m.get("created_time"), "open": m.get("open_time"),
                 "close": m.get("close_time"), "t0": t0, "peak_share": round(vol[tpk] / tot, 3) if tot else None,
                 "ncandles": len(cs)}
            for h in (0, 1, 6, 24):
                b, a, l = snap(cs, ts, t0 - h * 3600)
                r[f"b{h}"], r[f"a{h}"], r[f"l{h}"] = b, a, l
            r["vol_pre"] = sum(vv(c) for c in cs if c["end_period_ts"] <= t0)
            rows.append(r)
json.dump(rows, open("kalshi_dataset.json", "w"))
print("rows", len(rows), "events", len({r["event"] for r in rows}))

"""Компактные часовые пути цен до t0 (за 30 ч) для симуляции лимитных заявок -> kalshi_paths.json
Запуск: .venv\\Scripts\\python build_paths.py   (требует kalshi_dataset.json и kalshi_raw)
"""
import json, glob, os
ds = {r["ticker"]: r for r in json.load(open("kalshi_dataset.json"))}
def f(x):
    try: return round(float(x), 4)
    except Exception: return None
def g(d, k): return d.get(k + "_dollars", d.get(k))
out = {}
for fn in sorted(glob.glob("kalshi_raw/*.json")):
    d = json.load(open(fn))
    for t, cs in d.get("candles", {}).items():
        r = ds.get(t)
        if not r: continue
        t0 = r["t0"]
        rows = []
        for c in cs:
            e = c["end_period_ts"]
            if t0 - 30 * 3600 <= e <= t0:
                p = c.get("price", {})
                rows.append([e - t0, f(g(c["yes_bid"], "close")), f(g(c["yes_ask"], "close")),
                             f(g(c["yes_bid"], "low")), f(g(c["yes_ask"], "high")),
                             f(g(p, "high")), f(g(p, "low")), f(c.get("volume_fp", c.get("volume")))])
        out[t] = rows
json.dump(out, open("kalshi_paths.json", "w"), separators=(",", ":"))
print("markets", len(out))

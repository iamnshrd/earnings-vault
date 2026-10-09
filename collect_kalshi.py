"""Сбор истории Kalshi mention-рынков: живые + архивные события и часовые свечи.
Запуск:  .venv\\Scripts\\python collect_kalshi.py
Результат: kalshi_raw\\<SERIES>.json (можно запускать повторно — готовые серии пропускаются).
"""
import json, os, sys, time, datetime as dt
from kalshi_client import K

SERIES = ["AAL", "AAOI", "AAP", "AAPL", "ABNB", "AC", "ACA", "ACI", "ACN", "ADBE", "ADOBE", "ALIBABA", "ALK", "ALLY", "AMAT", "AMC", "AMD", "AMZN", "ANF", "ARITZIA", "AS", "ASTS", "ATZ", "AVAV", "AVGO", "AXP", "AZO", "BA", "BAC", "BB", "BJ", "BLK", "BULL", "C", "CALM", "CAR", "CAVA", "CBRL", "CBRS", "CCL", "CELH", "CHWY", "CIEN", "CMG", "COHR", "COINBASE", "COST", "CRCL", "CRM", "CRWD", "CRWV", "CVNA", "DAL", "DASH", "DE", "DEER", "DELL", "DIS", "DKNG", "DKS", "DOCUSIGN", "DOLLARGENERAL", "DPZ", "DUOL", "EA", "EBAY", "ETOR", "F", "FDX", "FIG", "FUTU", "GEV", "GIS", "GM", "GME", "GOOGL", "GRAB", "GS", "HD", "HIMS", "HLT", "HOOD", "HPE", "INTC", "INTU", "ISRG", "JNJ", "JPM", "KKR", "KLAR", "KMX", "KO", "KR", "KTOS", "LEVI", "LLY", "LMT", "LOW", "LUCID", "LULU", "LUNR", "LYFT", "M", "MA", "MCD", "MCO", "MDT", "MELI", "META", "MKC", "MRVL", "MS", "MSFT", "MSTR", "MTN", "MU", "NBIS", "NFLX", "NIO", "NKE", "NVDA", "NYT", "OKLO", "ON", "ORCL", "PANW", "PATH", "PEP", "PG", "PGR", "PLTR", "PSKY", "PYPL", "QCOM", "RACE", "RDDT", "RIVN", "RKLB", "ROKU", "ROST", "RY", "SBUX", "SFM", "SHOP", "SJM", "SNAP", "SNOW", "SPCX", "SPOT", "STZ", "SYUM", "TFC", "TGT", "TLN", "TOL", "TOST", "TSLA", "TSMC", "TTWO", "UAL", "UBER", "ULTA", "URBN", "V", "VSCO", "VST", "VZ", "WEN", "WFC", "WING", "WMT", "YETI", "YOU", "YUM", "ZETA", "ZM", "ZS"]
OUT = "kalshi_raw"
os.makedirs(OUT, exist_ok=True)
k = K()

def ts(s):
    return int(dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())

try:
    print("cutoff:", json.dumps(k.cutoff()))
except Exception as e:
    print("cutoff failed:", e)

for i, s in enumerate(SERIES, 1):
    fn = os.path.join(OUT, s + ".json")
    if os.path.exists(fn):
        try:
            if json.load(open(fn)).get("v") == 2:
                continue
        except Exception:
            pass
    sticker = "KXEARNINGSMENTION" + s
    try:
        live = k.events(sticker)
        hist = k.hist_markets(series=sticker)
    except Exception as e:
        print(i, s, "ERR", e); continue
    markets = {}
    for ev in live:
        for m in ev.get("markets", []):
            markets[m["ticker"]] = m
    for m in hist:
        markets.setdefault(m["ticker"], m)
    by_event = {}
    for m in markets.values():
        by_event.setdefault(m["event_ticker"], []).append(m)
    candles = {}
    for et, ms in by_event.items():
        try:
            b = max(ts(m["close_time"]) for m in ms)
            a = max(min(ts(m["open_time"]) for m in ms), b - 5 * 86400)
            got = k.candles_batch([m["ticker"] for m in ms], a, b, 60)
            for m in ms:
                c = got.get(m["ticker"])
                if not c:
                    try:
                        c = k.hist_candles(m["ticker"], a, b, 60)
                    except Exception:
                        c = []
                candles[m["ticker"]] = c
        except Exception as e:
            print("  candle err", et, e)
    json.dump({"v": 2, "markets": list(markets.values()), "candles": candles}, open(fn, "w"))
    print(i, len(SERIES), s, "events", len(by_event), "markets", len(markets), "live", len(live), "hist", len(hist), flush=True)
print("DONE")

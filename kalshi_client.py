"""Минимальный клиент публичного API Kalshi (рыночные данные, без ключей).
Зависит только от requests (уже есть в .venv). Не тестировался из облака — сети до Kalshi там нет.
Использование:  from kalshi_client import K; k=K(); print(k.cutoff())
"""
import time, requests

BASE = "https://external-api.kalshi.com/trade-api/v2"   # запасной: https://api.elections.kalshi.com/trade-api/v2

class K:
    def __init__(self, base=BASE, rps=10):
        self.base, self.s, self.gap, self.last = base, requests.Session(), 1.0 / rps, 0.0

    def get(self, path, **params):
        params = {k: v for k, v in params.items() if v is not None}
        for attempt in range(6):
            wait = self.gap - (time.time() - self.last)
            if wait > 0: time.sleep(wait)
            self.last = time.time()
            r = self.s.get(self.base + path, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(2 ** attempt); continue
            r.raise_for_status()
            return r.json()
        raise RuntimeError("429 retries exhausted: " + path)

    def pages(self, path, key, **params):
        cur = None
        while True:
            d = self.get(path, cursor=cur, **params)
            yield from d.get(key, [])
            cur = d.get("cursor")
            if not cur: return

    # --- границы архива ---
    def cutoff(self):
        return self.get("/historical/cutoff")

    # --- события/рынки: живые и исторические ---
    def events(self, series, status="settled"):
        return list(self.pages("/events", "events", series_ticker=series, status=status,
                               with_nested_markets="true", limit=200))

    def hist_markets(self, series=None, event=None):
        return list(self.pages("/historical/markets", "markets", series_ticker=series,
                               event_ticker=event, limit=1000))

    # --- свечи ---
    def candles_batch(self, tickers, start_ts, end_ts, period=60):
        """по 25 тикеров за запрос (лимит 10000 свечей); не более 10000 свечей суммарно -> режем на группы."""
        out = {}
        for i in range(0, len(tickers), 25):
            d = self.get("/markets/candlesticks", market_tickers=",".join(tickers[i:i+25]),
                         start_ts=start_ts, end_ts=end_ts, period_interval=period)
            for m in d.get("markets", []):
                out[m["market_ticker"]] = m["candlesticks"]
        return out

    def hist_candles(self, ticker, start_ts, end_ts, period=60):
        d = self.get(f"/historical/markets/{ticker}/candlesticks",
                     start_ts=start_ts, end_ts=end_ts, period_interval=period)
        return d.get("candlesticks", [])

    def trades(self, ticker, min_ts=None, max_ts=None):
        return list(self.pages("/markets/trades", "trades", ticker=ticker, min_ts=min_ts, max_ts=max_ts, limit=1000))

if __name__ == "__main__":
    k = K()
    print(k.cutoff())

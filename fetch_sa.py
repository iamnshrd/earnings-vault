"""Скачивает транскрипты (earnings + конференции/инвестор-дни) с stockanalysis.com с 2025-01-01.
Запуск: .venv\Scripts\python fetch_sa.py      Результат: sa_raw\<TICKER>\<date>_<id>.txt и sa_index.json
Повторный запуск докачивает только недостающее.
"""
import requests, re, os, json, time, html, datetime as dt
TICKERS = ["AAL", "AAOI", "AAP", "AAPL", "ABNB", "ACA", "ACI", "ACN", "ADBE", "BABA", "ALK", "ALLY", "AMAT", "AMC", "AMD", "AMZN", "ANF", "AS", "ASTS", "AVAV", "AVGO", "AXP", "AZO", "BA", "BAC", "BB", "BJ", "BLK", "BULL", "C", "CALM", "CAR", "CAVA", "CBRL", "CCL", "CELH", "CHWY", "CIEN", "CMG", "COHR", "COIN", "COST", "CRCL", "CRM", "CRWD", "CRWV", "CVNA", "DAL", "DASH", "DE", "DELL", "DIS", "DKNG", "DKS", "DOCU", "DG", "DPZ", "DUOL", "EA", "EBAY", "ETOR", "F", "FDX", "FIG", "FUTU", "GEV", "GIS", "GM", "GME", "GOOGL", "GRAB", "GS", "HD", "HIMS", "HLT", "HOOD", "HPE", "INTC", "INTU", "ISRG", "JNJ", "JPM", "KKR", "KLAR", "KMX", "KO", "KR", "KTOS", "LEVI", "LLY", "LMT", "LOW", "LCID", "LULU", "LUNR", "LYFT", "M", "MA", "MCD", "MCO", "MDT", "MELI", "META", "MKC", "MRVL", "MS", "MSFT", "MSTR", "MTN", "MU", "NBIS", "NFLX", "NIO", "NKE", "NVDA", "NYT", "OKLO", "ON", "ORCL", "PANW", "PATH", "PEP", "PG", "PGR", "PLTR", "PSKY", "PYPL", "QCOM", "RACE", "RDDT", "RIVN", "RKLB", "ROKU", "ROST", "RY", "SBUX", "SFM", "SHOP", "SJM", "SNAP", "SNOW", "SPCX", "SPOT", "STZ", "TFC", "TGT", "TLN", "TOL", "TOST", "TSLA", "TSM", "TTWO", "UAL", "UBER", "ULTA", "URBN", "V", "VSCO", "VST", "VZ", "WEN", "WFC", "WING", "WMT", "YETI", "YOU", "YUM", "ZETA", "ZM", "ZS"]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"}
S = requests.Session(); S.headers.update(UA)
SINCE = "2025-01-01"
os.makedirs("sa_raw", exist_ok=True)
idx_fn = "sa_index.json"
INDEX = json.load(open(idx_fn)) if os.path.exists(idx_fn) else {}

def get(url):
    for a in range(5):
        try:
            r = S.get(url, timeout=30)
            if r.status_code == 200: return r.text
            if r.status_code == 404: return None
            time.sleep(3 * (a + 1))
        except Exception:
            time.sleep(3 * (a + 1))
    return None

def parse_list(h, t):
    out = []
    for m in re.finditer(r'href="/stocks/%s/transcripts/(\d+-[a-z0-9-]+)/"[^>]*>([^<]+)</a>' % t.lower(), h):
        tail = h[m.end(): m.end() + 1500]
        dm = re.search(r'([A-Z][a-z]{2} \d{1,2}, \d{4})', tail)
        if not dm: continue
        d = dt.datetime.strptime(dm.group(1), "%b %d, %Y").date().isoformat()
        out.append({"slug": m.group(1), "title": html.unescape(m.group(2)).strip(), "date": d})
    seen = set(); res = []
    for o in out:
        if o["slug"] in seen: continue
        seen.add(o["slug"]); res.append(o)
    return res

def parse_tr(h):
    i = h.find('id="transcript-panel-full"')
    if i < 0: return None
    h = h[i:]
    j = h.find('id="transcript-panel-', 30)
    if j > 0: h = h[:j]
    lines, head = [], []
    for m in re.finditer(r'<div[^>]*>([^<]{1,150})</div>|<p[^>]*>(.*?)</p>', h, re.S):
        if m.group(1) is not None:
            tx = html.unescape(m.group(1)).strip()
            if tx: head.append(tx)
        else:
            body = html.unescape(re.sub(r'<[^>]+>', '', m.group(2)))
            body = re.sub(r'\s+', ' ', body).strip()
            if not body: continue
            if head:
                spk = head[0]; role = head[1] if len(head) > 1 else ""
                lines.append(f"## {spk} | {role}"); head = []
            lines.append(body)
    return "\n".join(lines)

for n, t in enumerate(TICKERS, 1):
    h = get(f"https://stockanalysis.com/stocks/{t.lower()}/transcripts/")
    if not h:
        print(n, t, "no list"); continue
    items = [o for o in parse_list(h, t) if o["date"] >= SINCE]
    os.makedirs(os.path.join("sa_raw", t), exist_ok=True)
    got = 0
    for o in items:
        fn = os.path.join("sa_raw", t, f'{o["date"]}_{o["slug"][:80]}.txt')
        key = t + "/" + o["slug"]
        if os.path.exists(fn):
            INDEX[key] = dict(o, ticker=t, file=fn); continue
        time.sleep(1.0)
        th = get(f'https://stockanalysis.com/stocks/{t.lower()}/transcripts/{o["slug"]}/')
        tx = parse_tr(th) if th else None
        if not tx:
            continue
        open(fn, "w", encoding="utf-8").write(f'TITLE: {o["title"]}\nDATE: {o["date"]}\n' + tx)
        INDEX[key] = dict(o, ticker=t, file=fn); got += 1
    json.dump(INDEX, open(idx_fn, "w"), indent=0)
    print(n, len(TICKERS), t, "items", len(items), "new", got, flush=True)
    time.sleep(1.0)
print("DONE", len(INDEX))

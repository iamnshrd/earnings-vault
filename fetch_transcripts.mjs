// Usage (PowerShell, in this folder):
//   $env:FINNHUB_KEY="your_key"; node fetch_transcripts.mjs            # all companies
//   $env:FINNHUB_KEY="your_key"; node fetch_transcripts.mjs NKE MU     # only these tickers
// Needs Node 18+. Safe to re-run: existing files are skipped.
import fs from 'node:fs';
import path from 'node:path';

const KEY = process.env.FINNHUB_KEY;
if (!KEY) { console.error('Set FINNHUB_KEY env var'); process.exit(1); }
const YEARS = 5;
const DELAY_MS = 1100; // free tier: 60 req/min
const root = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const companies = JSON.parse(fs.readFileSync(path.join(root, 'companies.json'), 'utf8'));
const only = process.argv.slice(2).map(s => s.toUpperCase());
const sleep = ms => new Promise(r => setTimeout(r, ms));
const cutoff = new Date(); cutoff.setFullYear(cutoff.getFullYear() - YEARS);

async function api(p, params) {
  const url = `https://finnhub.io/api/v1${p}?${new URLSearchParams({ ...params, token: KEY })}`;
  for (let i = 0; i < 5; i++) {
    await sleep(DELAY_MS);
    const r = await fetch(url);
    if (r.status === 429) { await sleep(15000); continue; }
    if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
    return r.json();
  }
  throw new Error('rate limited');
}

const log = [];
for (const c of companies) {
  if (only.length && !only.includes(c.ticker)) continue;
  const dir = path.join(root, c.folder);
  fs.mkdirSync(dir, { recursive: true });
  let list;
  try { list = (await api('/stock/transcripts/list', { symbol: c.symbol })).transcripts || []; }
  catch (e) { console.error(`${c.ticker}: list failed: ${e.message}`); log.push({ ticker: c.ticker, error: e.message }); if (/403|access/i.test(e.message)) { console.error('Likely premium-only endpoint; stopping.'); break; } continue; }
  const recent = list.filter(t => new Date(t.time) >= cutoff);
  console.log(`${c.ticker}: ${recent.length}/${list.length} transcripts in last ${YEARS}y`);
  for (const t of recent) {
    const d = (t.time || '').slice(0, 10);
    const base = path.join(dir, `${d}_${t.year}Q${t.quarter}`);
    if (fs.existsSync(base + '.txt')) continue;
    try {
      const x = await api('/stock/transcripts', { id: t.id });
      fs.writeFileSync(base + '.json', JSON.stringify(x, null, 1));
      const txt = (x.transcript || []).map(s => `[${s.session || ''}] ${s.name}${s.speech ? '' : ''}:\n${(s.speech || []).join('\n')}`).join('\n\n');
      fs.writeFileSync(base + '.txt', `${c.company} (${c.ticker}) ${t.title || ''}\n${t.time}\n\n${txt}`);
    } catch (e) { console.error(`${c.ticker} ${t.id}: ${e.message}`); log.push({ ticker: c.ticker, id: t.id, error: e.message }); }
  }
}
fs.writeFileSync(path.join(root, 'fetch_log.json'), JSON.stringify(log, null, 1));
console.log('done, errors:', log.length);

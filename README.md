# earnings-vault — сырые данные проекта earnings

Приватное хранилище данных для [`earnings`](https://github.com/iamnshrd/earnings)
(ex-ante досье по Kalshi mention markets).

**Агенты, собирающие досье, этот репозиторий не клонируют и не читают.**
Доступ к нему есть только у детерминированных скриптов (GitHub Actions в `earnings`,
по токену с правом чтения): они собирают для каждого прогона папку
`runs/<TICKER>_<дата>/` с транскриптами строго до cutoff и метаданными рынка.
Так транскрипт целевого звонка и результаты рынков физически недоступны агенту.

## Содержимое

| Путь | Что это |
|---|---|
| `transcripts/` | транскрипты звонков (discountingcashflows), только добавлять |
| `sa_raw/`, `sa_index.json` | транскрипты stockanalysis.com с 2025-01-01, только добавлять |
| `kalshi_raw/` | история Kalshi mention-рынков по сериям (события, страйки, свечи, результаты) |
| `kalshi_dataset.json`, `kalshi_paths.json` | сжатая история: цены до звонка, часовые пути |
| `companies.json`, `manifest.json`, `fetch_log.*` | список компаний, журналы загрузок |
| `fetch_*.py`, `fetch_transcripts.mjs` | загрузчики транскриптов |
| `collect_kalshi.py`, `kalshi_client.py`, `build_dataset.py`, `build_paths.py` | сбор и сжатие истории Kalshi |
| `tools/kalshi_meta.py` | безопасный вывод метаданных рынка (без цен и результатов) |

Правила: в `transcripts/` и `sa_raw/` ничего не удалять и не перезаписывать.
Журналы результатов и постмортемы сюда не класть.

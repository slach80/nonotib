# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

College soccer recruiting portfolio for Noah Lach (Class of 2028, #16 Midfielder/Forward), deployed on GitHub Pages. The repo has two distinct parts:

1. **Static recruiting site** — 6 HTML pages showcasing Noah's profile, target colleges, ID camps, scholarships, test prep, and an interactive college map
2. **Python monitoring backend** — `monitor/monitor.py` scrapes ~30 college soccer sites weekly and sends Telegram alerts on coaching changes or new camp postings

See `TODO.md` for known gaps: coach contact research needed for ~20 schools, open question on access control (Netlify password protection is the leading option), and a future family site expansion.

## Development

No build step. Edit HTML files directly; push to `main` to deploy via GitHub Pages.

To run the monitor manually:
```bash
cd monitor
python monitor.py
```

Monitor dependencies:
```bash
pip install requests beautifulsoup4 python-dotenv ollama
```

Monitor requires `monitor/.env` with `NOAH_ALERT_BOT_TOKEN` (gitignored). Uses local Ollama at `192.168.1.70:11434` (model `llama3.1:8b`) for AI analysis of scraped changes.

## Architecture

### Frontend (6 HTML pages)

All pages share the same inline CSS design system — no external stylesheets. CSS variables in each `<style>` block define the color palette (`--accent: #b8ff2e`, `--text: #0f1a2e`, etc.).

| Page | Purpose |
|------|---------|
| `index.html` | Hero profile, stats, journey timeline, video highlights, academics, target schools, contact |
| `colleges.html` | College program analysis with filterable cards by division (D1/D2/NAIA) and region |
| `map.html` | Interactive Leaflet.js map of all ~30 target colleges; filters by division/region with fly-to |
| `camps.html` | ID camp directory grouped by region with date badges (Confirmed/TBD) |
| `scholarships.html` | Scholarship opportunities with deadlines, amounts, eligibility tags |
| `testprep.html` | ACT/SAT prep plan, PSAT dates, score-sending strategy, reading list, progress tracker |

Navigation is duplicated across all pages (no shared includes). When updating nav, edit all 6 files. The hamburger mobile menu is activated at `<960px`.

`map.html` is the only page with an external JS dependency: Leaflet.js via CDN + CartoDB Voyager tiles.

### Division badge colors (consistent across pages)
- D1: red `#b71c1c`
- D2: blue `#0060c0`
- NAIA: gold `#9a6800`

### Backend (`monitor/monitor.py`)

- **Change detection**: MD5-hashes scraped page content against `data/baseline.json`; alerts on diff
- **AI summarization**: Sends diffs to local Ollama for plain-English summaries
- **Alerts**: Telegram bot `@NoahAlert_Bot`; `data/chat_id.txt` stores the registered chat ID (gitignored)
- **Scheduled**: Cron-driven, not a daemon

### Data files (gitignored)
- `data/baseline.json` — cached scrape snapshots
- `data/chat_id.txt` — Telegram chat registration
- `monitor/.env` — bot token
- `monitor/monitor.log` — runtime log

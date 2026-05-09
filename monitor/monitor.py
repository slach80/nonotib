#!/usr/bin/env python3
"""
Noah Lach Recruiting Monitor
Weekly check: coach page changes, roster analysis, scholarship deadlines, camp discovery.
Uses Scrapling for fetching (Cloudflare-resistant) + Ollama (llama3.1:8b) for AI analysis.
"""

import os, json, re, hashlib, datetime, requests, time, sys, logging
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv

logging.getLogger("scrapling").setLevel(logging.ERROR)
from scrapling.fetchers import Fetcher, StealthyFetcher

# ── Config ─────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
ENV_FILE = Path(__file__).parent / ".env"
load_dotenv(ENV_FILE)

BOT_TOKEN = os.getenv("NOAH_ALERT_BOT_TOKEN")
CHAT_ID_FILE = DATA_DIR / "chat_id.txt"
OLLAMA_URL = "http://192.168.1.70:11434/api/generate"
OLLAMA_MODEL = "qwen3:8b-32k"
BASELINE_FILE = DATA_DIR / "baseline.json"
ROSTER_SNAPSHOT_FILE = DATA_DIR / "roster_snapshot.json"
METRICS_FILE = DATA_DIR / "metrics.json"
ALERT_DAYS = [30, 7, 1]
SUCCESS_RATE_THRESHOLD = 0.70  # Alert if success rate drops below 70%
ENABLE_RETRY = True  # Retry failed fetches after delay
RETRY_DELAY_MINUTES = 15  # Wait 15min before retry (allows transient issues to resolve)
RETRY_THRESHOLD = 0.50  # Only retry if initial success rate < 50% (indicates systemic issue)

_FETCHER = Fetcher()
_STEALTH = None  # lazy-init on first 403/block

# ── Target schools ──────────────────────────────────────────────────
SCHOOLS = [
    # KC / Missouri
    {"name": "Rockhurst University",       "div": "D2",   "coaches": "https://rockhursthawks.com/sports/mens-soccer/coaches",     "roster": "https://rockhursthawks.com/sports/mens-soccer/roster"},
    {"name": "MidAmerica Nazarene",        "div": "NAIA", "coaches": "https://mnusports.com/sports/mens-soccer/coaches",           "roster": "https://mnusports.com/sports/mens-soccer/roster"},
    {"name": "University of Saint Mary",   "div": "NAIA", "coaches": "https://gospires.com/sports/mens-soccer/coaches",            "roster": "https://gospires.com/sports/mens-soccer/roster"},
    {"name": "Park University",            "div": "NAIA", "coaches": "https://parkathletics.com/sports/mens-soccer/coaches",       "roster": "https://parkathletics.com/sports/mens-soccer/roster"},
    {"name": "Drury University",           "div": "D2",   "coaches": "https://drurypanthers.com/sports/mens-soccer/coaches",       "roster": "https://drurypanthers.com/sports/mens-soccer/roster"},
    {"name": "Maryville University",       "div": "D2",   "coaches": "https://maryvillesaints.com/sports/mens-soccer/coaches",     "roster": "https://maryvillesaints.com/sports/mens-soccer/roster"},
    {"name": "William Jewell College",     "div": "NAIA", "coaches": "https://jewellcardinals.com/sports/msoc/coaches",            "roster": "https://jewellcardinals.com/sports/msoc/roster"},
    {"name": "Truman State University",    "div": "D2",   "coaches": "https://trumanbulldogs.com/sports/msoc/coaches",             "roster": "https://trumanbulldogs.com/sports/msoc/roster"},
    {"name": "Southwest Baptist",          "div": "D2",   "coaches": "https://www.sbubearcats.com/sports/msoc/coaches",            "roster": "https://www.sbubearcats.com/sports/msoc/roster"},
    {"name": "Evangel University",         "div": "NAIA", "coaches": "https://www.evangelathletics.com/sports/mens-soccer/coaches","roster": "https://www.evangelathletics.com/sports/mens-soccer/roster"},
    {"name": "Lindenwood University",      "div": "D1",   "coaches": "https://lindenwoodlions.com/sports/msoc/coaches",            "roster": "https://lindenwoodlions.com/sports/msoc/roster"},
    {"name": "Saint Louis University",     "div": "D1",   "coaches": "https://www.slubillikens.com/sports/msoc/coaches",           "roster": "https://www.slubillikens.com/sports/msoc/roster"},
    {"name": "UMKC",                       "div": "D1",   "coaches": "https://www.kcroos.com/sports/msoc/coaches",                 "roster": "https://www.kcroos.com/sports/msoc/roster"},
    {"name": "Missouri State University",  "div": "D1",   "coaches": "https://missouristatebears.com/sports/msoc/coaches",         "roster": "https://missouristatebears.com/sports/msoc/roster"},
    # Florida
    {"name": "University of Tampa",        "div": "D2",   "coaches": None,                                                         "roster": None},  # Cloudflare-blocked
    {"name": "Florida Southern College",   "div": "D2",   "coaches": "https://fscmocs.com/sports/msoc/coaches",                    "roster": "https://fscmocs.com/sports/msoc/roster"},
    {"name": "Southeastern University",    "div": "NAIA", "coaches": "https://fire.seu.edu/sports/msoc/coaches",                   "roster": "https://fire.seu.edu/sports/msoc/roster"},
    {"name": "Saint Leo University",       "div": "D2",   "coaches": "https://saintleolions.com/sports/msoc/coaches",              "roster": "https://saintleolions.com/sports/msoc/roster"},
    {"name": "Eckerd College",             "div": "D2",   "coaches": "https://www.eckerdtritons.com/sports/mens-soccer/coaches",   "roster": "https://www.eckerdtritons.com/sports/mens-soccer/roster"},
    {"name": "Lynn University",            "div": "D2",   "coaches": "https://www.lynnfightingknights.com/sports/msoc/coaches",    "roster": "https://www.lynnfightingknights.com/sports/msoc/roster"},
    {"name": "Warner University",          "div": "NAIA", "coaches": "https://warnerroyals.com/sports/msoc/coaches",               "roster": "https://warnerroyals.com/sports/msoc/roster"},
    {"name": "Univ. of South Florida",     "div": "D1",   "coaches": "https://gousfbulls.com/sports/msoc/coaches",                 "roster": "https://gousfbulls.com/sports/msoc/roster"},
    # California
    {"name": "Point Loma Nazarene",        "div": "D2",   "coaches": "https://plnusealions.com/sports/msoc/coaches",               "roster": "https://plnusealions.com/sports/msoc/roster"},
    {"name": "Cal State San Marcos",       "div": "D2",   "coaches": "https://csusmcougars.com/sports/msoc/coaches",               "roster": "https://csusmcougars.com/sports/msoc/roster"},
    {"name": "Cal State East Bay",         "div": "D2",   "coaches": "https://eastbaypioneers.com/sports/msoc/coaches",            "roster": "https://eastbaypioneers.com/sports/msoc/roster"},
    {"name": "San Diego State",            "div": "D1",   "coaches": "https://www.goaztecs.com/sports/mens-soccer/coaches",        "roster": "https://www.goaztecs.com/sports/mens-soccer/roster"},
    {"name": "San Jose State",             "div": "D1",   "coaches": "https://www.sjsuspartans.com/sports/mens-soccer/coaches",    "roster": "https://www.sjsuspartans.com/sports/mens-soccer/roster"},
    {"name": "University of San Diego",    "div": "D1",   "coaches": "https://usdtoreros.com/sports/msoc/coaches",                 "roster": "https://usdtoreros.com/sports/msoc/roster"},
]

# ── Scholarship deadlines to track ─────────────────────────────────
SCHOLARSHIPS = [
    {"name": "Missouri Bright Flight",         "deadline": "07-31", "recurring": True,  "url": "https://dhe.mo.gov/ppc/brightflight.php"},
    {"name": "Coca-Cola Scholars",             "deadline": "10-15", "recurring": True,  "url": "https://www.coca-colascholarsfoundation.org"},
    {"name": "SEARAC SE Asian Scholarships",   "deadline": "rolling","recurring": False, "url": "https://www.searac.org"},
    {"name": "United Soccer Coaches Scholar",  "deadline": "01-15", "recurring": True,  "url": "https://www.unitedsoccercoaches.org/scholarships"},
    {"name": "National Soccer HOF Scholarship","deadline": "04-01", "recurring": True,  "url": "https://www.nationalsoccerhof.com"},
    {"name": "NATA Scholarship",               "deadline": "02-15", "recurring": True,  "url": "https://www.nata.org/professional-development/scholarships"},
    {"name": "SHAPE America Scholarship",      "deadline": "12-15", "recurring": True,  "url": "https://www.shapeamerica.org/awards/scholarships"},
    {"name": "SS&C Dependent (check HR)",      "deadline": "rolling","recurring": False, "url": "https://www.ssctech.com/about/careers"},
    {"name": "AmeriLife Dependent (check HR)", "deadline": "rolling","recurring": False, "url": "https://amerilife.com/careers"},
]

# ── Telegram ────────────────────────────────────────────────────────
def get_chat_id():
    if CHAT_ID_FILE.exists():
        return CHAT_ID_FILE.read_text().strip()
    return None

def send_telegram(message, parse_mode="Markdown"):
    chat_id = get_chat_id()
    if not chat_id:
        print(f"[WARN] No chat_id yet. Message would be:\n{message}")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for mode in [parse_mode, None]:
        try:
            payload = {"chat_id": chat_id, "text": message}
            if mode:
                payload["parse_mode"] = mode
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code == 200:
                return
            elif "can't parse" in r.text.lower() and mode:
                continue
            else:
                print(f"[ERROR] Telegram send failed: {r.text}")
                return
        except Exception as e:
            print(f"[ERROR] Telegram: {e}")
            return

def poll_for_chat_id():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    r = requests.get(url, timeout=10)
    data = r.json()
    for update in data.get("result", []):
        msg = update.get("message") or update.get("channel_post")
        if msg:
            cid = str(msg["chat"]["id"])
            CHAT_ID_FILE.write_text(cid)
            print(f"[INFO] Captured chat_id: {cid}")
            return cid
    return None

# ── Scraping ────────────────────────────────────────────────────────
def fetch_page(url, timeout=20, record_metrics=True):
    """
    Fetch URL using Scrapling; falls back to StealthyFetcher on 403/429/503.
    Returns (page, method) tuple where method is 'scrapling', 'stealthy', or None on failure.
    """
    global _STEALTH
    if not url:
        return None, None

    # Try Scrapling first
    try:
        page = _FETCHER.get(url, timeout=timeout)
        if page.status in (403, 429, 503):
            raise ValueError(f"blocked ({page.status})")
        return page, 'scrapling'
    except Exception as e1:
        # Fallback to StealthyFetcher
        try:
            if _STEALTH is None:
                _STEALTH = StealthyFetcher()
            page = _STEALTH.fetch(url, timeout=timeout + 10)
            return page, 'stealthy'
        except Exception as e2:
            if record_metrics:
                print(f"    [SKIP] {url}: {e2}")
            return None, None

def page_hash(page_tuple):
    """Extract hash from page. Accepts both (page, method) tuple and bare page for compatibility."""
    page = page_tuple[0] if isinstance(page_tuple, tuple) else page_tuple
    if not page:
        return None
    html = page.html_content if hasattr(page, 'html_content') else page
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return hashlib.md5(text.encode()).hexdigest(), text[:4000]

# ── Roster analysis ─────────────────────────────────────────────────
# Short-form only (e.g. "Fr.", "So.") — avoids double-counting with long form
YEAR_MAP_SHORT = {
    'fr.': 'Fr', 'so.': 'So', 'jr.': 'Jr', 'sr.': 'Sr', 'gr.': 'Gr', 'gs': 'Gr', '5th': 'Gr',
}
# Long-form only — used when short form not present
YEAR_MAP_LONG = {
    'freshman': 'Fr', 'sophomore': 'So', 'junior': 'Jr', 'senior': 'Sr',
    'graduate student': 'Gr', 'graduate': 'Gr',
}
YEAR_MAP = {**YEAR_MAP_SHORT, **YEAR_MAP_LONG}

def extract_roster_counts(page_tuple):
    """Extract Fr/So/Jr/Sr/Gr counts from a Scrapling page object. Accepts (page, method) tuple or bare page."""
    page = page_tuple[0] if isinstance(page_tuple, tuple) else page_tuple
    counts = {'Fr': 0, 'So': 0, 'Jr': 0, 'Sr': 0, 'Gr': 0}
    if not page:
        return counts, 0

    # Primary: Sidearm Athletics — each player has both short ("Fr.") and long ("Freshman")
    # in the same element, so count only short-form abbreviations to avoid doubling.
    year_els = page.css(".sidearm-roster-player-academic-year")
    if year_els:
        for el in year_els:
            t = el.text.strip().lower()
            y = YEAR_MAP_SHORT.get(t)
            if y:
                counts[y] += 1
        total = sum(counts.values())
        if total > 0:
            return counts, total

    # Fallback A: SJSU-style card layout
    card_els = page.css('[class*="profile-field__value--basic"]')
    if card_els:
        for el in card_els:
            t = el.text.strip().lower()
            y = YEAR_MAP_LONG.get(t) or YEAR_MAP_SHORT.get(t)
            if y:
                counts[y] += 1
        total = sum(counts.values())
        if total > 0:
            return counts, total

    # Fallback B: generic [class*="class"] — used by some sites (e.g. goaztecs.com)
    class_els = page.css('[class*="class"]')
    if class_els:
        for el in class_els:
            t = el.text.strip().lower()
            y = YEAR_MAP_LONG.get(t) or YEAR_MAP_SHORT.get(t)
            if y:
                counts[y] += 1
        total = sum(counts.values())
        if total > 0:
            return counts, total

    # Fallback C: scan all <td> cells (plain HTML tables)
    for td in page.css("td"):
        t = td.text.strip().lower()
        y = YEAR_MAP_SHORT.get(t) or YEAR_MAP_LONG.get(t)
        if y:
            counts[y] += 1
    return counts, sum(counts.values())

def recruitment_window(counts, div):
    """
    Score recruitment opportunity for Noah (Class of 2028, enters Fall 2028).
    Current Sophomores → Seniors when Noah arrives (their departure = openings).
    Current Juniors → open slots one year before Noah enters.
    Current Freshmen → Juniors competing directly with Noah.
    """
    total = sum(counts.values())
    if total == 0:
        return "unknown", 0
    noah_era_openings = counts['So']            # graduating when Noah arrives
    leaving_2027 = counts['Jr']                  # open space one year early
    leaving_now = counts['Sr'] + counts['Gr']   # immediate openings, may recruit ahead
    competition = counts['Fr']                   # will be Juniors competing for Noah's slot
    score = (noah_era_openings * 3 + leaving_2027 * 2 + leaving_now) - (competition * 1.5)
    pct_so = counts['So'] / total
    if score >= 15 and pct_so >= 0.15:
        window = "HIGH"
    elif score >= 8:
        window = "MEDIUM"
    else:
        window = "LOW"
    return window, round(score, 1)

def analyze_roster_opportunity(school_name, div, counts, score, window):
    """Ask Ollama for a 1-sentence recommendation based on roster data."""
    total = sum(counts.values())
    prompt = f"""College soccer recruiting analysis for Noah Lach (Class of 2028, MLS Next midfielder/forward, Kansas City MO).

School: {school_name} ({div})
Roster: Fr={counts['Fr']}, So={counts['So']}, Jr={counts['Jr']}, Sr={counts['Sr']}, Gr={counts['Gr']} (total={total})
Recruitment window: {window} (score={score})

Noah enters Fall 2028. Current Sophomores will be Seniors then — their departure = key scholarship openings.

Write ONE sentence (max 20 words) advising whether Noah should prioritize contact with this program and why."""

    try:
        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 60}
        }, timeout=45)
        return r.json().get("response", "").strip()
    except Exception:
        return None

# ── Ollama AI analysis ──────────────────────────────────────────────
def analyze_change(school_name, old_text, new_text, category="coaching staff"):
    prompt = f"""You are analyzing a college soccer program page for recruiting purposes.

School: {school_name}
Category: {category}

OLD content (previous week):
{old_text[:2000]}

NEW content (this week):
{new_text[:2000]}

Identify ONLY significant changes relevant to a high school soccer recruit:
- Coach hired or fired
- New head coach named
- Roster size changes
- Camp dates announced
- Contact info changed
- Program changes (division change, program suspended, etc.)

If nothing significant changed, reply with exactly: NO_CHANGE
If something changed, reply with a 1-2 sentence summary starting with: CHANGE:"""

    try:
        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 200}
        }, timeout=60)
        return r.json().get("response", "").strip()
    except Exception as e:
        return f"ERROR: {e}"

def search_camps(school_name, school_url):
    if not school_url:
        return None
    camps_url = school_url.replace("/coaches", "/camps")
    page, _ = fetch_page(camps_url, record_metrics=False)
    if not page:
        return None
    html = page.html_content if hasattr(page, 'html_content') else page
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)[:3000]

    prompt = f"""Search this athletics page for men's soccer ID camp, recruiting camp, or prospect camp information for {school_name}.

Page text:
{text}

If you find a camp with a specific date in 2025 or 2026, reply: CAMP_FOUND: [camp name] - [date] - [cost if listed]
If no specific camp date is found, reply: NO_CAMP"""

    try:
        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 100}
        }, timeout=45)
        return r.json().get("response", "").strip()
    except Exception:
        return None

def search_new_schools():
    prompt = """A high school sophomore midfielder/forward (Class of 2028, 3.5 GPA, MLS Next Academy Division, Kansas City MO) is looking for college soccer programs. He wants Physical Therapy, Athletic Training, or Sports Medicine degrees.

Currently targeting: Kansas City/Missouri, Tampa Bay FL, San Jose/San Diego CA regions.
Divisions: NAIA, NCAA D1, NCAA D2.

Suggest 3 schools NOT commonly listed that could be good fits — include school name, division, conference, city, and degree program available. Focus on schools that actively recruit Midwest MLS Next players. Be specific and concise."""

    try:
        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.4, "num_predict": 300}
        }, timeout=60)
        return r.json().get("response", "").strip()
    except Exception:
        return None

# ── Deadline tracking ───────────────────────────────────────────────
def check_deadlines():
    today = datetime.date.today()
    year = today.year
    alerts = []
    for sch in SCHOLARSHIPS:
        if sch["deadline"] == "rolling":
            continue
        try:
            month, day = map(int, sch["deadline"].split("-"))
            deadline = datetime.date(year, month, day)
            if deadline < today:
                deadline = datetime.date(year + 1, month, day)
            days_left = (deadline - today).days
            for threshold in ALERT_DAYS:
                if days_left <= threshold:
                    alerts.append({
                        "name": sch["name"],
                        "deadline": deadline.strftime("%B %d, %Y"),
                        "days_left": days_left,
                        "url": sch["url"]
                    })
                    break
        except Exception:
            continue
    return alerts

# ── Baseline management ─────────────────────────────────────────────
def load_baseline():
    if BASELINE_FILE.exists():
        return json.loads(BASELINE_FILE.read_text())
    return {}

def save_baseline(data):
    BASELINE_FILE.write_text(json.dumps(data, indent=2))

def load_roster_snapshot():
    if ROSTER_SNAPSHOT_FILE.exists():
        return json.loads(ROSTER_SNAPSHOT_FILE.read_text())
    return {}

def save_roster_snapshot(data):
    ROSTER_SNAPSHOT_FILE.write_text(json.dumps(data, indent=2))

# ── Metrics tracking ────────────────────────────────────────────────
def load_metrics():
    if METRICS_FILE.exists():
        return json.loads(METRICS_FILE.read_text())
    return {"runs": [], "school_stats": {}}

def save_metrics(data):
    METRICS_FILE.write_text(json.dumps(data, indent=2))

def record_run_metrics(metrics, run_stats):
    """Record metrics for this run and maintain rolling 30-day history."""
    today = str(datetime.date.today())

    # Add this run
    metrics["runs"].append({
        "date": today,
        "timestamp": datetime.datetime.now().isoformat(),
        "total_schools": run_stats["total"],
        "coaches_success": run_stats["coaches_success"],
        "coaches_failed": run_stats["coaches_failed"],
        "rosters_success": run_stats.get("rosters_success", 0),
        "rosters_failed": run_stats.get("rosters_failed", 0),
        "success_rate": run_stats["coaches_success"] / run_stats["total"] if run_stats["total"] > 0 else 0,
        "fetch_methods": run_stats.get("fetch_methods", {}),
    })

    # Keep only last 30 days
    cutoff = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    metrics["runs"] = [r for r in metrics["runs"] if r["date"] >= cutoff]

    save_metrics(metrics)

def update_school_stats(metrics, school_name, url, success, method=None, error=None):
    """Track per-school fetch statistics."""
    if school_name not in metrics["school_stats"]:
        metrics["school_stats"][school_name] = {
            "total_attempts": 0,
            "successes": 0,
            "failures": 0,
            "consecutive_failures": 0,
            "last_success": None,
            "last_failure": None,
            "last_error": None,
            "fetch_methods": {},
        }

    stats = metrics["school_stats"][school_name]
    stats["total_attempts"] += 1

    if success:
        stats["successes"] += 1
        stats["consecutive_failures"] = 0
        stats["last_success"] = str(datetime.date.today())
        if method:
            stats["fetch_methods"][method] = stats["fetch_methods"].get(method, 0) + 1
    else:
        stats["failures"] += 1
        stats["consecutive_failures"] += 1
        stats["last_failure"] = str(datetime.date.today())
        if error:
            stats["last_error"] = str(error)[:200]

def get_success_rate_alert(metrics):
    """Check if recent success rate is below threshold."""
    if not metrics["runs"]:
        return None

    # Check last 3 runs
    recent = metrics["runs"][-3:]
    if len(recent) < 2:
        return None

    avg_rate = sum(r["success_rate"] for r in recent) / len(recent)

    if avg_rate < SUCCESS_RATE_THRESHOLD:
        failing_schools = []
        for name, stats in metrics["school_stats"].items():
            if stats["consecutive_failures"] >= 2:
                failing_schools.append(f"{name} ({stats['consecutive_failures']} failures)")

        return {
            "avg_rate": avg_rate,
            "threshold": SUCCESS_RATE_THRESHOLD,
            "recent_runs": len(recent),
            "failing_schools": failing_schools[:10],  # Top 10
        }

    return None

# ── Roster report ────────────────────────────────────────────────────
def run_roster_report(verbose=False, send_tg=True):
    """Scrape all roster pages, score recruitment windows, optionally send Telegram summary."""
    print(f"\n{'='*60}")
    print(f"Roster Analysis — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    results = []
    snapshot = load_roster_snapshot()

    for school in SCHOOLS:
        name = school["name"]
        div = school["div"]
        roster_url = school.get("roster")

        if not roster_url:
            print(f"  [SKIP] {name} — no roster URL")
            results.append({"name": name, "div": div, "window": "skip", "score": 0,
                            "counts": {}, "total": 0, "url": roster_url, "rec": None})
            continue

        print(f"  → {name}")
        page = fetch_page(roster_url)
        counts, total = extract_roster_counts(page)
        window, score = recruitment_window(counts, div)

        rec = None
        if verbose and total > 0:
            rec = analyze_roster_opportunity(name, div, counts, score, window)

        results.append({"name": name, "div": div, "window": window, "score": score,
                        "counts": counts, "total": total, "url": roster_url, "rec": rec})

        snapshot[name] = {"counts": counts, "total": total, "score": score,
                          "window": window, "checked": str(datetime.date.today())}

        star = "⭐" if window == "HIGH" else ("◆" if window == "MEDIUM" else "·")
        c = counts
        print(f"    {star} {window} (score={score}) Fr={c['Fr']} So={c['So']} Jr={c['Jr']} Sr={c['Sr']} Gr={c['Gr']} total={total}")
        if rec:
            print(f"    💬 {rec}")
        time.sleep(1)

    save_roster_snapshot(snapshot)

    # Summary table
    print(f"\n{'─'*65}")
    print(f"{'SCHOOL':<30} {'DIV':<6} {'WIN':<8} {'SCORE':>6}  ROSTER")
    print(f"{'─'*65}")
    for r in sorted(results, key=lambda x: -x["score"]):
        if r["window"] == "skip":
            continue
        c = r["counts"]
        roster_str = f"Fr:{c.get('Fr',0)} So:{c.get('So',0)} Jr:{c.get('Jr',0)} Sr:{c.get('Sr',0)}"
        star = "⭐" if r["window"] == "HIGH" else ("◆" if r["window"] == "MEDIUM" else " ")
        print(f"{star} {r['name']:<28} {r['div']:<6} {r['window']:<8} {r['score']:>6}  {roster_str}")
    print(f"{'─'*65}")

    if not send_tg:
        return

    if not get_chat_id():
        print("[WARN] No chat_id — skipping Telegram")
        return

    high = [r for r in results if r["window"] == "HIGH"]
    med  = [r for r in results if r["window"] == "MEDIUM"]

    lines = [f"📊 *Roster Recruitment Window Analysis*\n_{datetime.date.today().strftime('%B %d, %Y')}_\n"]
    lines.append(f"Noah Class of 2028 — {len(SCHOOLS)} schools analyzed\n")

    if high:
        lines.append(f"*⭐ HIGH Priority ({len(high)} schools)*")
        for r in sorted(high, key=lambda x: -x["score"]):
            c = r["counts"]
            lines.append(f"• *{r['name']}* ({r['div']}) score={r['score']}")
            lines.append(f"  Fr:{c.get('Fr',0)} So:{c.get('So',0)} Jr:{c.get('Jr',0)} Sr:{c.get('Sr',0)} Gr:{c.get('Gr',0)}")
            if r.get("rec"):
                lines.append(f"  _{r['rec']}_")
        lines.append("")

    if med:
        lines.append(f"*◆ MEDIUM Priority ({len(med)} schools)*")
        for r in sorted(med, key=lambda x: -x["score"]):
            lines.append(f"• *{r['name']}* ({r['div']}) score={r['score']}")
        lines.append("")

    lines.append("_Score = So×3 + Jr×2 + (Sr+Gr) − Fr×1.5 — @NoahAlert_Bot_")
    send_telegram("\n".join(lines))
    print(f"\n📬 Roster report sent to Telegram")

# ── Main monitor run ─────────────────────────────────────────────────
def run_monitor():
    print(f"\n{'='*60}")
    print(f"Noah Lach Recruiting Monitor — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    if not get_chat_id():
        print("[INFO] No chat_id found — polling for first message...")
        cid = poll_for_chat_id()
        if not cid:
            print("[WARN] Send any message to @NoahAlert_Bot first to register.")
            return

    baseline = load_baseline()
    metrics = load_metrics()
    school_changes = []
    camp_updates = []

    # Track this run's statistics
    run_stats = {
        "total": len([s for s in SCHOOLS if s["coaches"] is not None]),
        "coaches_success": 0,
        "coaches_failed": 0,
        "fetch_methods": {},
        "failed_schools": [],  # Track which schools failed for retry
    }

    # ── 1. School coach page monitoring ─────────────────────────────
    print("[1/4] Checking school coach pages...")
    for school in SCHOOLS:
        name = school["name"]
        url = school["coaches"]
        if not url:
            print(f"  [SKIP] {name} — no coaches URL")
            continue
        print(f"  → {name}")
        page, method = fetch_page(url)

        if not page:
            run_stats["coaches_failed"] += 1
            run_stats["failed_schools"].append(school)
            update_school_stats(metrics, name, url, success=False, error="fetch failed")
            continue

        # Track success
        run_stats["coaches_success"] += 1
        run_stats["fetch_methods"][method] = run_stats["fetch_methods"].get(method, 0) + 1
        update_school_stats(metrics, name, url, success=True, method=method)

        result = page_hash((page, method))
        if not result:
            continue
        new_hash, new_text = result

        old_entry = baseline.get(name, {})
        old_hash = old_entry.get("hash")
        old_text = old_entry.get("text", "")

        if old_hash and new_hash != old_hash:
            print(f"    [CHANGED] Analyzing with Ollama...")
            analysis = analyze_change(name, old_text, new_text)
            if analysis and not analysis.startswith("NO_CHANGE") and not analysis.startswith("ERROR"):
                school_changes.append({"school": name, "div": school["div"], "change": analysis, "url": url})
                print(f"    ⚡ {analysis}")
        elif not old_hash:
            print(f"    [NEW] Baseline recorded")

        baseline[name] = {"hash": new_hash, "text": new_text, "url": url, "checked": str(datetime.date.today())}
        time.sleep(1)

    # Print run summary
    success_rate = run_stats["coaches_success"] / run_stats["total"] if run_stats["total"] > 0 else 0
    print(f"\n  📊 Fetch summary: {run_stats['coaches_success']}/{run_stats['total']} successful ({success_rate:.1%})")
    if run_stats["fetch_methods"]:
        methods_str = ", ".join(f"{m}={c}" for m, c in run_stats["fetch_methods"].items())
        print(f"     Methods: {methods_str}")

    # ── RETRY LOGIC: If success rate is very low, wait and retry failures ────
    if ENABLE_RETRY and success_rate < RETRY_THRESHOLD and run_stats["coaches_failed"] > 0:
        print(f"\n  ⚠️  Low success rate ({success_rate:.0%}) detected — likely transient network/DNS issue")
        print(f"  ⏳ Waiting {RETRY_DELAY_MINUTES} minutes before retrying {run_stats['coaches_failed']} failed schools...")

        # Wait for network/DNS to stabilize
        time.sleep(RETRY_DELAY_MINUTES * 60)

        print(f"\n  🔄 Retrying {len(run_stats['failed_schools'])} failed schools...")
        retry_success = 0
        retry_failed = 0

        for school in run_stats['failed_schools']:
            name = school["name"]
            url = school["coaches"]
            print(f"  → {name} (retry)")
            page, method = fetch_page(url)

            if not page:
                retry_failed += 1
                update_school_stats(metrics, name, url, success=False, error="retry failed")
                continue

            # Success on retry!
            retry_success += 1
            run_stats["coaches_success"] += 1
            run_stats["coaches_failed"] -= 1
            run_stats["fetch_methods"][method] = run_stats["fetch_methods"].get(method, 0) + 1
            update_school_stats(metrics, name, url, success=True, method=method)

            result = page_hash((page, method))
            if result:
                new_hash, new_text = result
                old_entry = baseline.get(name, {})
                old_hash = old_entry.get("hash")
                old_text = old_entry.get("text", "")

                if old_hash and new_hash != old_hash:
                    print(f"    [CHANGED] Analyzing with Ollama...")
                    analysis = analyze_change(name, old_text, new_text)
                    if analysis and not analysis.startswith("NO_CHANGE") and not analysis.startswith("ERROR"):
                        school_changes.append({"school": name, "div": school["div"], "change": analysis, "url": url})
                        print(f"    ⚡ {analysis}")
                elif not old_hash:
                    print(f"    [NEW] Baseline recorded")

                baseline[name] = {"hash": new_hash, "text": new_text, "url": url, "checked": str(datetime.date.today())}

            time.sleep(1)

        final_rate = run_stats["coaches_success"] / run_stats["total"] if run_stats["total"] > 0 else 0
        print(f"\n  ✅ Retry complete: {retry_success} recovered, {retry_failed} still failed")
        print(f"  📊 Final success rate: {run_stats['coaches_success']}/{run_stats['total']} ({final_rate:.1%})")
        success_rate = final_rate  # Update for metrics

    # ── 2. Camp discovery ────────────────────────────────────────────
    print("\n[2/4] Checking camps for TBD schools...")
    TBD_SCHOOLS = [
        "Rockhurst University", "Park University", "University of Saint Mary",
        "Maryville University", "Southwest Baptist", "Evangel University",
        "Saint Leo University", "Lynn University", "Warner University",
        "Point Loma Nazarene", "Cal State East Bay", "San Jose State",
    ]
    for school in SCHOOLS:
        if school["name"] in TBD_SCHOOLS:
            print(f"  → {school['name']}")
            result = search_camps(school["name"], school["coaches"])
            if result and result.startswith("CAMP_FOUND:"):
                camp_info = result.replace("CAMP_FOUND:", "").strip()
                old_camp = baseline.get(f"camp_{school['name']}", "")
                if camp_info != old_camp:
                    camp_updates.append({"school": school["name"], "info": camp_info})
                    baseline[f"camp_{school['name']}"] = camp_info
                    print(f"    ⚡ {camp_info}")
            time.sleep(1)

    # ── 3. Deadline warnings ─────────────────────────────────────────
    print("\n[3/4] Checking scholarship deadlines...")
    deadline_alerts = check_deadlines()
    for d in deadline_alerts:
        print(f"  ⚠️  {d['name']} — {d['days_left']} days left ({d['deadline']})")

    # ── 4. New school discovery (monthly) ────────────────────────────
    today = datetime.date.today()
    last_discovery = baseline.get("last_school_discovery", "2000-01-01")
    new_schools_suggestion = None
    if (today - datetime.date.fromisoformat(last_discovery)).days >= 30:
        print("\n[4/4] Searching for new qualifying schools (monthly)...")
        new_schools_suggestion = search_new_schools()
        baseline["last_school_discovery"] = str(today)
        if new_schools_suggestion:
            print(f"  → Got suggestions")
    else:
        print(f"\n[4/4] School discovery skipped (last run: {last_discovery})")

    # ── 5. Roster window analysis (quarterly) ────────────────────────
    last_roster = baseline.get("last_roster_check", "2000-01-01")
    roster_alerts = []
    if (today - datetime.date.fromisoformat(last_roster)).days >= 90:
        print("\n[5/5] Running quarterly roster window analysis...")
        prev_snapshot = {}
        if ROSTER_SNAPSHOT_FILE.exists():
            try:
                prev_snapshot = json.loads(ROSTER_SNAPSHOT_FILE.read_text())
            except Exception:
                pass
        new_snapshot = {}
        for school in SCHOOLS:
            name = school["name"]
            url = school.get("roster")
            if not url:
                continue
            page = fetch_page(url)
            counts, total = extract_roster_counts(page)
            if total == 0:
                continue
            window, score = recruitment_window(counts, school["div"])
            new_snapshot[name] = {"window": window, "score": score, "counts": counts}
            prev = prev_snapshot.get(name, {})
            prev_window = prev.get("window")
            if prev_window and prev_window != window:
                roster_alerts.append({
                    "school": name, "div": school["div"],
                    "old": prev_window, "new": window, "score": score,
                })
                print(f"  ⚡ {name}: {prev_window} → {window} (score={score})")
            else:
                print(f"  → {name}: {window} (score={score})")
            time.sleep(1)
        ROSTER_SNAPSHOT_FILE.write_text(json.dumps(new_snapshot, indent=2))
        baseline["last_roster_check"] = str(today)
        print(f"  Snapshot saved ({len(new_snapshot)} schools)")
    else:
        print(f"\n[5/5] Roster check skipped (last run: {last_roster}, next in {90 - (today - datetime.date.fromisoformat(last_roster)).days}d)")

    save_baseline(baseline)

    # ── Record metrics and check for success rate alerts ─────────────
    record_run_metrics(metrics, run_stats)
    success_alert = get_success_rate_alert(metrics)

    if success_alert:
        print(f"\n⚠️  SUCCESS RATE ALERT: {success_alert['avg_rate']:.1%} (threshold: {success_alert['threshold']:.0%})")
        print(f"   Persistent failures: {len(success_alert['failing_schools'])} schools")
        for fail in success_alert['failing_schools'][:5]:
            print(f"     • {fail}")

    save_metrics(metrics)

    # ── Build and send Telegram report ───────────────────────────────
    total_alerts = len(school_changes) + len(camp_updates) + len(deadline_alerts) + len(roster_alerts)

    if total_alerts == 0 and not new_schools_suggestion and not success_alert:
        msg = (f"✅ *Weekly Check Complete* — {today.strftime('%b %d, %Y')}\n\n"
               f"No changes detected across {len(SCHOOLS)} target schools. All clear.\n\n"
               f"Fetch success: {run_stats['coaches_success']}/{run_stats['total']} ({success_rate:.0%})\n\n"
               f"_@NoahAlert_Bot_")
        send_telegram(msg)
        print("\n✅ All clear — sent summary to Telegram")
    else:
        lines = [f"🔔 *Noah Lach Recruiting Alert*\n_{today.strftime('%B %d, %Y')}_\n"]

        if school_changes:
            lines.append(f"*⚡ {len(school_changes)} School Change(s) Detected*")
            for c in school_changes:
                summary = c['change'].replace('CHANGE:', '').strip()
                lines.append(f"• *{c['school']}* ({c['div']})\n  {summary}\n  [View]({c['url']})")
            lines.append("")

        if camp_updates:
            lines.append(f"*🏕 {len(camp_updates)} Camp Update(s)*")
            for c in camp_updates:
                lines.append(f"• *{c['school']}*: {c['info']}")
            lines.append("")

        if deadline_alerts:
            lines.append(f"*⏰ {len(deadline_alerts)} Deadline Warning(s)*")
            for d in deadline_alerts:
                emoji = "🚨" if d['days_left'] <= 7 else "⚠️"
                lines.append(f"{emoji} *{d['name']}*\n  {d['days_left']} days left — {d['deadline']}\n  [Apply]({d['url']})")
            lines.append("")

        if roster_alerts:
            lines.append(f"*📊 {len(roster_alerts)} Roster Window Change(s)*")
            for r in roster_alerts:
                lines.append(f"• *{r['school']}* ({r['div']}): {r['old']} → {r['new']} (score={r['score']})")
            lines.append("")

        if new_schools_suggestion:
            lines.append(f"*🏫 New School Suggestions (Monthly)*\n{new_schools_suggestion}")

        if success_alert:
            lines.append(f"\n⚠️ *System Alert: Low Success Rate*")
            lines.append(f"Recent fetch success: {success_alert['avg_rate']:.0%} (threshold: {success_alert['threshold']:.0%})")
            if success_alert['failing_schools']:
                lines.append(f"Persistent failures ({len(success_alert['failing_schools'])}):")
                for fail in success_alert['failing_schools'][:5]:
                    lines.append(f"  • {fail}")

        lines.append(f"\n_Checked {len(SCHOOLS)} schools ({run_stats['coaches_success']}/{run_stats['total']} ok) — @NoahAlert_Bot_")
        send_telegram("\n".join(lines))
        print(f"\n📬 Sent alert: {total_alerts} items")

    print("\nDone.\n")

# ── Setup / CLI ───────────────────────────────────────────────────────
def setup():
    print("Setup: Send any message to @NoahAlert_Bot on Telegram, then press Enter...")
    input()
    cid = poll_for_chat_id()
    if cid:
        print(f"✅ Registered! Chat ID: {cid}")
        send_telegram("🤖 *NoahAlert Bot* is now active!\n\nYou'll receive weekly recruiting alerts for:\n• Coach/roster changes\n• Camp announcements\n• Scholarship deadlines\n• New school suggestions\n\nNext check runs on the weekly schedule.")
    else:
        print("❌ No message found. Make sure you messaged @NoahAlert_Bot first.")

def show_metrics():
    """Display success rate metrics and school statistics."""
    metrics = load_metrics()
    if not metrics.get("runs"):
        print("No metrics data yet. Run the monitor first.")
        return

    print(f"\n{'='*70}")
    print("Monitor Success Rate Metrics")
    print(f"{'='*70}\n")

    # Recent runs summary
    print("Recent Runs (last 10):")
    print(f"{'Date':<12} {'Success':>8} {'Failed':>7} {'Rate':>6}  {'Methods'}")
    print("─" * 70)
    for run in metrics["runs"][-10:]:
        methods = ", ".join(f"{k}={v}" for k, v in run.get("fetch_methods", {}).items()) or "—"
        print(f"{run['date']:<12} {run['coaches_success']:>8} {run['coaches_failed']:>7} {run['success_rate']:>6.1%}  {methods}")

    # Overall stats
    if len(metrics["runs"]) >= 3:
        recent_avg = sum(r["success_rate"] for r in metrics["runs"][-3:]) / 3
        print(f"\nRecent 3-run average: {recent_avg:.1%}")
        if recent_avg < SUCCESS_RATE_THRESHOLD:
            print(f"⚠️  Below threshold ({SUCCESS_RATE_THRESHOLD:.0%})")

    # School failure stats
    failing = [(name, stats) for name, stats in metrics["school_stats"].items()
               if stats["consecutive_failures"] >= 2]
    if failing:
        failing.sort(key=lambda x: x[1]["consecutive_failures"], reverse=True)
        print(f"\n{'─'*70}")
        print(f"Schools with Persistent Failures ({len(failing)}):")
        print(f"{'School':<30} {'Consecutive':>12} {'Last Success':<15} {'Error'}")
        print("─" * 70)
        for name, stats in failing[:15]:
            last_ok = stats.get("last_success", "never")[:10]
            err = (stats.get("last_error") or "")[:30]
            print(f"{name:<30} {stats['consecutive_failures']:>12} {last_ok:<15} {err}")

    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "setup":
        setup()
    elif cmd == "test":
        if not get_chat_id():
            print("Run setup first: python3 monitor.py setup")
        else:
            send_telegram("🧪 *Test message* — @NoahAlert_Bot is working correctly!")
            print("Test message sent!")
    elif cmd == "roster":
        verbose = "--verbose" in sys.argv
        run_roster_report(verbose=verbose, send_tg=True)
    elif cmd == "roster-silent":
        verbose = "--verbose" in sys.argv
        run_roster_report(verbose=verbose, send_tg=False)
    elif cmd == "metrics":
        show_metrics()
    else:
        run_monitor()

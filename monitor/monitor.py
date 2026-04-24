#!/usr/bin/env python3
"""
Noah Lach Recruiting Monitor
Runs weekly — checks coaches, rosters, camps, scholarships, new schools.
Uses local Ollama (llama3.1:8b) on LACHGAMING for AI analysis.
Sends alerts via @NoahAlert_Bot Telegram.
"""

import os, json, re, hashlib, datetime, requests, time, sys
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ── Config ─────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
ENV_FILE = Path(__file__).parent / ".env"
load_dotenv(ENV_FILE)

BOT_TOKEN = os.getenv("NOAH_ALERT_BOT_TOKEN")
CHAT_ID_FILE = DATA_DIR / "chat_id.txt"
OLLAMA_URL = "http://192.168.1.70:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"
BASELINE_FILE = DATA_DIR / "baseline.json"
DEADLINES_FILE = DATA_DIR / "deadlines.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NoahLachMonitor/1.0)"}
ALERT_DAYS = [30, 7, 1]

# ── Target schools with their athletics coach pages ─────────────────
SCHOOLS = [
    # KC / Missouri
    {"name": "Rockhurst University",       "div": "D2",   "url": "https://rockhursthawks.com/sports/mens-soccer/coaches"},
    {"name": "MidAmerica Nazarene",        "div": "NAIA", "url": "https://mnusports.com/sports/mens-soccer/coaches"},
    {"name": "University of Saint Mary",   "div": "NAIA", "url": "https://gospires.com/sports/mens-soccer/coaches"},
    {"name": "Park University",            "div": "NAIA", "url": "https://parkathletics.com/sports/mens-soccer/coaches"},
    {"name": "Drury University",           "div": "D2",   "url": "https://drurypanthers.com/sports/mens-soccer/coaches"},
    {"name": "Maryville University",       "div": "D2",   "url": "https://maryvillesaints.com/sports/mens-soccer/coaches"},
    {"name": "Missouri Western State",     "div": "D2",   "url": "https://mwsugriffons.com/sports/msoc/coaches"},  # Cloudflare protected — manual check
    {"name": "William Jewell College",     "div": "NAIA", "url": "https://jewellcardinals.com/sports/msoc/coaches"},
    {"name": "Truman State University",    "div": "D2",   "url": "https://trumanbulldogs.com/sports/msoc/coaches"},
    {"name": "Southwest Baptist",          "div": "D2",   "url": "https://www.sbubearcats.com/sports/msoc/coaches"},
    {"name": "Evangel University",         "div": "NAIA", "url": "https://www.evangelathletics.com/sports/mens-soccer/coaches"},
    {"name": "Lindenwood University",      "div": "D1",   "url": "https://lindenwoodlions.com/sports/msoc/coaches"},
    {"name": "Saint Louis University",     "div": "D1",   "url": "https://www.slubillikens.com/sports/msoc/coaches"},
    {"name": "UMKC",                       "div": "D1",   "url": "https://www.kcroos.com/sports/msoc/coaches"},
    {"name": "Missouri State University",  "div": "D1",   "url": "https://missouristatebears.com/sports/msoc/coaches"},
    # Florida
    {"name": "University of Tampa",        "div": "D2",   "url": "https://tampaspartans.com/sports/msoc/coaches"},
    {"name": "Florida Southern College",   "div": "D2",   "url": "https://fscmocs.com/sports/msoc/coaches"},
    {"name": "Southeastern University",    "div": "NAIA", "url": "https://fire.seu.edu/sports/msoc/coaches"},
    {"name": "Saint Leo University",       "div": "D2",   "url": "https://saintleolions.com/sports/msoc/coaches"},
    {"name": "Eckerd College",             "div": "D2",   "url": "https://www.eckerdtritons.com/sports/mens-soccer/coaches"},
    {"name": "Lynn University",            "div": "D2",   "url": "https://www.lynnfightingknights.com/sports/msoc/coaches"},
    {"name": "Warner University",          "div": "NAIA", "url": "https://warnerroyals.com/sports/msoc/coaches"},
    {"name": "Univ. of South Florida",     "div": "D1",   "url": "https://gousfbulls.com/sports/msoc/coaches"},
    # California
    {"name": "Point Loma Nazarene",        "div": "D2",   "url": "https://plnusealions.com/sports/msoc/coaches"},
    {"name": "Cal State San Marcos",       "div": "D2",   "url": "https://csusmcougars.com/sports/msoc/coaches"},
    {"name": "Cal State East Bay",         "div": "D2",   "url": "https://eastbaypioneers.com/sports/msoc/coaches"},
    {"name": "San Diego State",            "div": "D1",   "url": "https://www.goaztecs.com/sports/mens-soccer/roster"},
    {"name": "San Jose State",             "div": "D1",   "url": "https://www.sjsuspartans.com/sports/mens-soccer/roster"},
    {"name": "University of San Diego",    "div": "D1",   "url": "https://usdtoreros.com/sports/msoc/coaches"},
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

# ── Camp search queries ─────────────────────────────────────────────
CAMP_SEARCH_TERMS = [
    "men's soccer ID camp 2026 {school}",
    "soccer recruiting camp 2026 {school}",
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
    # Try with Markdown first, fall back to plain text if parse fails
    for mode in [parse_mode, None]:
        try:
            payload = {"chat_id": chat_id, "text": message}
            if mode:
                payload["parse_mode"] = mode
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code == 200:
                return
            elif "can't parse" in r.text.lower() and mode:
                continue  # retry without parse_mode
            else:
                print(f"[ERROR] Telegram send failed: {r.text}")
                return
        except Exception as e:
            print(f"[ERROR] Telegram: {e}")
            return

def poll_for_chat_id():
    """Poll Telegram updates to capture first message's chat_id."""
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
def fetch_page(url, timeout=20):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        return None

def page_hash(html):
    if not html:
        return None
    # Extract meaningful text only (strip scripts/styles)
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return hashlib.md5(text.encode()).hexdigest(), text[:4000]

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
        response = r.json().get("response", "").strip()
        return response
    except Exception as e:
        return f"ERROR: {e}"

def search_camps(school_name, school_url):
    """Search athletics camps page for new ID camp info."""
    camps_url = school_url.replace("/coaches", "/camps").replace("/coaches", "")
    html = fetch_page(camps_url)
    if not html:
        return None
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
    except:
        return None

def search_new_schools():
    """Ask Ollama to suggest new qualifying schools based on profile."""
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
    except Exception as e:
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
            # If deadline already passed this year, check next year
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
                    break  # Only send highest-priority alert
        except:
            continue
    return alerts

# ── Baseline management ─────────────────────────────────────────────
def load_baseline():
    if BASELINE_FILE.exists():
        return json.loads(BASELINE_FILE.read_text())
    return {}

def save_baseline(data):
    BASELINE_FILE.write_text(json.dumps(data, indent=2))

# ── Main monitor run ─────────────────────────────────────────────────
def run_monitor():
    print(f"\n{'='*60}")
    print(f"Noah Lach Recruiting Monitor — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    # Ensure we have a chat_id
    if not get_chat_id():
        print("[INFO] No chat_id found — polling for first message...")
        cid = poll_for_chat_id()
        if not cid:
            print("[WARN] Send any message to @NoahAlert_Bot first to register.")
            return

    baseline = load_baseline()
    alerts = []
    camp_updates = []
    school_changes = []

    # ── 1. School coach/roster page monitoring ──────────────────────
    print("[1/4] Checking school pages...")
    for school in SCHOOLS:
        name = school["name"]
        url = school["url"]
        print(f"  → {name}")
        html = fetch_page(url)
        if not html:
            print(f"    [SKIP] Could not fetch {url}")
            continue

        result = page_hash(html)
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
        time.sleep(1)  # Be polite to servers

    # ── 2. Camp discovery for TBD schools ─────────────────────────
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
            result = search_camps(school["name"], school["url"])
            if result and result.startswith("CAMP_FOUND:"):
                camp_info = result.replace("CAMP_FOUND:", "").strip()
                old_camp = baseline.get(f"camp_{school['name']}", "")
                if camp_info != old_camp:
                    camp_updates.append({"school": school["name"], "info": camp_info})
                    baseline[f"camp_{school['name']}"] = camp_info
                    print(f"    ⚡ {camp_info}")
            time.sleep(1)

    # ── 3. Deadline warnings ────────────────────────────────────────
    print("\n[3/4] Checking scholarship deadlines...")
    deadline_alerts = check_deadlines()
    for d in deadline_alerts:
        print(f"  ⚠️  {d['name']} — {d['days_left']} days left ({d['deadline']})")

    # ── 4. New school discovery (monthly, not weekly) ───────────────
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

    # ── Save updated baseline ───────────────────────────────────────
    save_baseline(baseline)

    # ── Build and send Telegram report ─────────────────────────────
    total_alerts = len(school_changes) + len(camp_updates) + len(deadline_alerts)

    if total_alerts == 0 and not new_schools_suggestion:
        msg = f"✅ *Weekly Check Complete* — {today.strftime('%b %d, %Y')}\n\nNo changes detected across {len(SCHOOLS)} target schools. All clear.\n\n_@NoahAlert_Bot_"
        send_telegram(msg)
        print("\n✅ All clear — sent summary to Telegram")
    else:
        # Build detailed report
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

        if new_schools_suggestion:
            lines.append(f"*🏫 New School Suggestions (Monthly)*\n{new_schools_suggestion}")

        lines.append(f"\n_Checked {len(SCHOOLS)} schools — @NoahAlert_Bot_")
        send_telegram("\n".join(lines))
        print(f"\n📬 Sent alert: {total_alerts} items")

    print("\nDone.\n")

# ── Setup command ────────────────────────────────────────────────────
def setup():
    """Run once to register your Telegram chat_id with the bot."""
    print("Setup: Send any message to @NoahAlert_Bot on Telegram, then press Enter...")
    input()
    cid = poll_for_chat_id()
    if cid:
        print(f"✅ Registered! Chat ID: {cid}")
        send_telegram("🤖 *NoahAlert Bot* is now active!\n\nYou'll receive weekly recruiting alerts for:\n• Coach/roster changes\n• Camp announcements\n• Scholarship deadlines\n• New school suggestions\n\nNext check runs on the weekly schedule.")
    else:
        print("❌ No message found. Make sure you messaged @NoahAlert_Bot first.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup()
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Send a test message
        if not get_chat_id():
            print("Run setup first: python3 monitor.py setup")
        else:
            send_telegram("🧪 *Test message* — @NoahAlert_Bot is working correctly!")
            print("Test message sent!")
    else:
        run_monitor()

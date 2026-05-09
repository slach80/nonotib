#!/usr/bin/env python3
"""
Export CRM data for Google Sheets Coach Outreach
Combines SCHOOLS data from monitor.py with roster snapshot scores.
"""

import json
import csv
from pathlib import Path
from monitor import SCHOOLS

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_FILE = ROOT / "coach_crm_data.csv"
ROSTER_SNAPSHOT = DATA_DIR / "roster_snapshot.json"


def load_roster_data():
    """Load roster snapshot with recruitment window scores."""
    if not ROSTER_SNAPSHOT.exists():
        print(f"Warning: {ROSTER_SNAPSHOT} not found. Run 'python monitor.py roster' first.")
        return {}
    return json.loads(ROSTER_SNAPSHOT.read_text())


def export_crm_csv():
    """Export school data + roster scores to CSV for Google Sheets import."""
    roster_data = load_roster_data()

    rows = []
    for school in SCHOOLS:
        name = school["name"]
        div = school["div"]
        coaches_url = school.get("coaches", "")

        # Get roster window score if available
        roster_info = roster_data.get(name, {})
        window = roster_info.get("window", "")
        score = roster_info.get("score", "")

        rows.append({
            "School": name,
            "Division": div,
            "Coach URL": coaches_url or "",
            "Roster Window": window,
            "Score": score,
            "Coach Name": "",
            "Coach Email": "",
            "Date Contacted": "",
            "Response Status": "",
            "Notes": ""
        })

    # Sort by score (highest first), then by school name
    rows.sort(key=lambda x: (-float(x["Score"]) if x["Score"] else 0, x["School"]))

    # Write CSV
    fieldnames = ["School", "Division", "Coach URL", "Roster Window", "Score",
                  "Coach Name", "Coach Email", "Date Contacted", "Response Status", "Notes"]

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Exported {len(rows)} schools to {OUTPUT_FILE}")
    print(f"   Sorted by recruitment window score (HIGH priority first)")
    print(f"\n📋 Next steps:")
    print(f"   1. Open Google Sheets and create a new spreadsheet")
    print(f"   2. Import {OUTPUT_FILE.name} (File > Import > Upload)")
    print(f"   3. Research and fill in Coach Name + Coach Email columns")
    print(f"   4. Install the Google Apps Script (see CoachOutreachCRM.gs)")


if __name__ == "__main__":
    export_crm_csv()

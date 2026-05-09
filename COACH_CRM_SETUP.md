# Coach Outreach CRM — Setup Guide

Gmail-based CRM for tracking Noah Lach's college soccer recruiting outreach using Google Sheets + Apps Script.

## Overview

**What it does:**
- Tracks 29 target schools with recruitment window scores
- Sends personalized coach emails from noahlach@gmail.com
- Records contact dates and response status
- Generates weekly digest of follow-ups needed
- Warns if emails sent with unfilled placeholders

**Tech stack:**
- Google Sheets (CRM database)
- Google Apps Script (automation + Gmail integration)
- Python export script (monitor.py → CSV)

---

## Step 1: Generate CRM Data

Run the export script to create a CSV with all schools + roster scores:

```bash
cd /home/slach/Projects/nonotib/monitor
python3 export_crm_data.py
```

This creates `coach_crm_data.csv` with columns:
- School, Division, Coach URL, Roster Window, Score
- Coach Name, Coach Email, Date Contacted, Response Status, Notes

Schools are pre-sorted by recruitment window score (HIGH priority first).

---

## Step 2: Import to Google Sheets

1. Go to https://sheets.google.com
2. Create a new spreadsheet: **"Noah Soccer Recruiting CRM"**
3. Import the CSV:
   - File → Import → Upload
   - Select `coach_crm_data.csv`
   - Import location: **Replace current sheet**
   - Separator type: **Comma**
4. Rename the sheet to **"Sheet1"** (or update `CONFIG.SHEET_NAME` in the Apps Script)

---

## Step 3: Research Coach Contacts

Fill in the **Coach Name** and **Coach Email** columns for each school.

**Where to find contacts:**
- Visit the "Coach URL" column links
- Check school athletics staff directories
- Look for "Contact Coach" sections on coach bio pages
- Use format: `FirstName LastName` for Coach Name

**Priority:** Focus on HIGH window schools first (top of the spreadsheet).

**Background agents are researching:**
- KC/MO region: 7 schools
- Tampa Bay region: 7 schools  
- California region: 5 schools

Results will be provided separately to paste into the sheet.

---

## Step 4: Install Google Apps Script

1. In your Google Sheet, go to: **Extensions → Apps Script**
2. Delete any default code in the editor
3. Open `/home/slach/Projects/nonotib/CoachOutreachCRM.gs`
4. Copy the entire file contents
5. Paste into the Apps Script editor
6. Update the configuration section:

```javascript
const CONFIG = {
  FROM_EMAIL: 'noahlach@gmail.com',
  PORTFOLIO_URL: 'https://slach80.github.io/nonotib',
  SPORTSRECRUITS_URL: '[PASTE_NOAH_SPORTSRECRUITS_URL_HERE]',  // ← Update this
  SHEET_NAME: 'Sheet1',  // Match your sheet name
  // ... rest stays default
};
```

7. Save the script: **Ctrl+S** (or Cmd+S on Mac)
8. Close the Apps Script tab
9. **Refresh your Google Sheet** — you should see a new menu: **"Coach Outreach"**

---

## Step 5: Authorize the Script

First time you run any function:

1. Click **Coach Outreach → Test Email Template**
2. Google will prompt: *"Authorization required"*
3. Click **Review permissions**
4. Select your Google account (noahlach@gmail.com)
5. Click **Advanced** → **Go to Noah Soccer Recruiting CRM (unsafe)**
6. Click **Allow**

The script now has permission to:
- Send emails via Gmail
- Read/write to your spreadsheet

---

## Step 6: Customize Email Placeholders

Before sending emails, fill in these placeholders in the Apps Script or manually per email:

**In the script** (line ~120, `buildEmailBody()` function):
- `[GPA]` → Noah's current GPA
- `[Year]` → SAT test year (e.g., "2026")
- `[Phone Number]` → Noah's contact phone

**Per school** (manually before sending):
- `[specific reason]` → Why interested in that school
  - Example: "your program's recent success in the conference championships and strong academic reputation"
  - This should be **personalized per school** — generic emails get no response

**Warning:** The script will auto-log in the Notes column if you send with unfilled placeholders.

---

## Usage Guide

### Send Email to One School

1. Click on the row for that school
2. **Coach Outreach → Send Email to Selected Row**
3. Confirm the coach name/email look correct
4. Email sent! The script auto-fills:
   - Date Contacted: today's date
   - Response Status: "Awaiting Response"

### Send Bulk Emails

1. **Coach Outreach → Send Bulk Emails (All Uncontacted)**
2. Confirm the dialog (shows how many emails will be sent)
3. Script sends to all rows where "Date Contacted" is empty
4. Rate limiting: max 90 emails/day (safety margin under Gmail's 100/day limit)
5. 500ms delay between sends to avoid triggering spam filters

### Weekly Digest

Run once per week to track progress:

1. **Coach Outreach → Generate Weekly Digest**
2. Script sends a Telegram alert with:
   - Total contacted vs uncontacted
   - This week's outreach count
   - Response rate
   - Schools needing follow-up (2+ weeks old, no response)
   - Next steps

### Test Email

Before sending to coaches, test the template:

1. **Coach Outreach → Test Email Template**
2. Sends a test email to noahlach@gmail.com using first row data
3. Review formatting, links, placeholders

---

## Email Template Structure

**Subject:**
```
Class of 2028 Midfielder - Noah Lach - [School Name]
```

**Body:**
```
Dear Coach [Last Name],

My name is Noah Lach, and I am a Class of 2028 center midfielder/forward 
from Sporting Kansas City Academy in Kansas City, Missouri.

I am very interested in your program at [School Name] because [specific reason].

Here is my recruiting portfolio: https://slach80.github.io/nonotib
Here is my SportsRecruits profile: [SPORTSRECRUITS_URL]

This past season, I competed at the MLS Next level with Sporting KC Academy.

My current GPA is [GPA] and I am preparing for SAT testing in [Year].

I would really appreciate any feedback on where I stand with your program 
and what I should focus on improving.

Thank you for your time, and I hope to speak with you soon.

Best regards,
Noah Lach
Midfielder/Forward | Class of 2028
Sporting Kansas City Academy
[Phone Number]
noahlach@gmail.com
Portfolio: https://slach80.github.io/nonotib
```

---

## Response Tracking

**Manually update these columns** when coaches respond:

1. **Response Status** options:
   - "Awaiting Response" (auto-set on send)
   - "Replied - Interested"
   - "Replied - Not Recruiting Class 2028"
   - "Replied - Will Follow Up"
   - "No Response"
   - "Follow-up Sent"

2. **Notes** column:
   - Record key info from coach replies
   - Camp invites, evaluation feedback, next steps
   - Script auto-logs warnings and errors here

---

## Follow-up Strategy

**From the email template guide:**
- Follow up every **3-4 weeks** with updates
- Personalized emails = conversations
- Generic emails = no response

**What to include in follow-ups:**
- Recent game highlights or tournament results
- New film links
- Updated academic achievements
- Upcoming showcase events where coaches can watch

---

## Gmail Quota Limits

**Personal Gmail account limits:**
- 100 emails/day max
- Script uses 90/day safety margin
- Quota resets at midnight Pacific Time

**If you hit the limit:**
- Script will stop and log error in Notes column
- Wait until next day to resume
- Consider spreading bulk sends across multiple days

---

## Troubleshooting

**"Authorization required" every time:**
- Apps Script permissions were revoked
- Re-authorize in Step 5

**Emails not sending:**
- Check Gmail quota (Settings → Quota dashboard)
- Verify FROM_EMAIL matches logged-in Google account
- Check spam folder for delivery confirmations

**"Coach Outreach" menu not appearing:**
- Refresh the Google Sheet
- Check Apps Script saved correctly
- Look for errors in Apps Script: Extensions → Apps Script → Execution log

**Script errors in Notes column:**
- `Invalid email` → Fix Coach Email column format
- `Already contacted` → Date Contacted not empty (prevents duplicates)
- `Missing data` → Coach Name or School is blank

---

## Maintenance

**Weekly:**
- Run Weekly Digest to review progress
- Update Response Status for schools that replied
- Add follow-up notes in Notes column

**Monthly:**
- Re-run `export_crm_data.py` if roster scores change
- Re-import CSV (will overwrite — export your filled contacts first!)
- Consider adding new schools based on monitor's suggestions

**After coach replies:**
- Mark Response Status immediately
- If interested, add to calendar for follow-ups in 3-4 weeks
- Update Notes with action items from their response

---

## Files Reference

| File | Purpose |
|------|---------|
| `monitor/export_crm_data.py` | Generate CSV from SCHOOLS + roster data |
| `coach_crm_data.csv` | Import file for Google Sheets |
| `CoachOutreachCRM.gs` | Google Apps Script automation code |
| `COACH_CRM_SETUP.md` | This setup guide |

---

## Next Steps After Setup

1. **Fill in coach contacts** for all HIGH window schools (agents researching)
2. **Update placeholders** in Apps Script (GPA, phone, SportsRecruits URL)
3. **Test with one school** using Test Email Template
4. **Review test email** in noahlach@gmail.com inbox
5. **Send first batch** (5-10 schools) to start building response data
6. **Track responses** and iterate on template based on what gets replies

---

## Security Notes

- Never commit coach email addresses to public repos
- Keep Google Sheet private (Share settings)
- Apps Script runs under your Google account permissions
- Script only accesses this specific spreadsheet + Gmail send
- Can revoke access anytime: Google Account → Security → Third-party apps

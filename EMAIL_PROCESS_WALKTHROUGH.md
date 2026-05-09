# Coach Email Process — Complete Walkthrough

Step-by-step guide showing exactly how the email system works from Google Sheet → Gmail.

---

## The Email Flow (Visual Diagram)

```
┌─────────────────────────────────────────────────────────────┐
│  Google Sheet — Noah Soccer Recruiting CRM                  │
│                                                              │
│  Row Example:                                                │
│  ┌──────────────┬──────┬──────────┬────────┬─────────────┐ │
│  │ School       │ Div  │ Coach    │ Email  │ Date        │ │
│  │              │      │ Name     │        │ Contacted   │ │
│  ├──────────────┼──────┼──────────┼────────┼─────────────┤ │
│  │ Rockhurst U  │ D2   │ John Doe │ jd@... │ [EMPTY]     │ │
│  └──────────────┴──────┴──────────┴────────┴─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↓
                    User Action:
                    Click "Coach Outreach" menu
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Google Apps Script — CoachOutreachCRM.gs                   │
│                                                              │
│  1. Read row data                                           │
│  2. Validate (has email? not contacted yet?)                │
│  3. Generate email content                                  │
│  4. Check for placeholders                                  │
│  5. Send via GmailApp                                       │
│  6. Update sheet with date + status                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Gmail — noahlach@gmail.com                                 │
│                                                              │
│  📧 Email sent with:                                        │
│     From: Noah Lach <noahlach@gmail.com>                   │
│     To: jd@rockhursthawks.com                              │
│     Subject: Class of 2028 Midfielder - Noah Lach -        │
│              Rockhurst University                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Google Sheet — Updated Row                                 │
│                                                              │
│  ┌──────────────┬──────┬──────────┬────────┬─────────────┐ │
│  │ Rockhurst U  │ D2   │ John Doe │ jd@... │ 05/07/2026  │ │
│  └──────────────┴──────┴──────────┴────────┴─────────────┘ │
│  ┌──────────────────┬────────────────────────────────────┐ │
│  │ Response Status  │ Notes                              │ │
│  ├──────────────────┼────────────────────────────────────┤ │
│  │ Awaiting Response│ [Auto-logged if placeholders]      │ │
│  └──────────────────┴────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step: Sending a Single Email

### Step 1: Select a School Row

In your Google Sheet, click on any row with:
- ✅ Coach Name filled in
- ✅ Coach Email filled in  
- ⚠️ Date Contacted is EMPTY

### Step 2: Open Menu

Click **Coach Outreach** → **Send Email to Selected Row**

### Step 3: Script Validates Data

The script checks:
```javascript
// ❌ Stops if email is missing
if (!coachEmail) {
  return error: 'No email address found for this coach.'
}

// ❌ Stops if already contacted (prevents duplicates)
if (dateContacted) {
  return error: 'Coach already contacted on 05/01/2026'
}

// ❌ Stops if school name is missing
if (!school) {
  return error: 'School name is missing.'
}

// ✅ All checks pass → continue
```

### Step 4: Generate Email Content

```javascript
// Subject line
buildEmailSubject(school)
→ "Class of 2028 Midfielder - Noah Lach - Rockhurst University"

// Body
buildEmailBody(school, coachName, format)
→ Greeting: "Dear Coach Doe," (uses last name from "John Doe")
→ Personalized content with school name
→ Links to portfolio + SportsRecruits
→ Placeholders: [GPA], [Year], [Phone Number], [specific reason]
```

### Step 5: Send Email via Gmail

```javascript
GmailApp.sendEmail(
  'jd@rockhursthawks.com',           // To
  'Class of 2028 Midfielder...',     // Subject
  'Dear Coach Doe...',               // Plain text body
  {
    from: 'noahlach@gmail.com',      // From
    htmlBody: '<p>Dear Coach...</p>', // HTML body
    name: 'Noah Lach'                // Display name
  }
)
```

### Step 6: Update Sheet

```javascript
// Mark as contacted
sheet.getRange(row, DATE_CONTACTED).setValue(new Date())
→ Cell shows: "05/07/2026"

// Set status
sheet.getRange(row, RESPONSE_STATUS).setValue('Awaiting Response')
```

### Step 7: Check for Placeholders

```javascript
// If email contains [brackets], add warning
if (emailBody.includes('[') && emailBody.includes(']')) {
  addNote: "[05/07/2026] WARNING: Email sent with unfilled placeholders..."
}
```

### Step 8: Show Confirmation

Dialog appears:
```
✅ Email sent successfully to John Doe at Rockhurst University!
```

---

## The Email That Gets Sent

### What the Coach Receives

**From:** Noah Lach <noahlach@gmail.com>  
**Subject:** Class of 2028 Midfielder - Noah Lach - Rockhurst University  

**Body (HTML formatted):**

---

Dear Coach Doe,

My name is Noah Lach, and I am a Class of 2028 center midfielder/forward from Sporting Kansas City Academy in Kansas City, Missouri.

I am very interested in your program at Rockhurst University because [specific reason - will be filled manually or left as placeholder].

Here is my recruiting portfolio: https://slach80.github.io/nonotib  
Here is my SportsRecruits profile: [YOUR_SPORTSRECRUITS_PROFILE_URL]

This past season, I competed at the MLS Next level with Sporting KC Academy.

My current GPA is [GPA] and I am preparing for SAT testing in [Year].

I would really appreciate any feedback on where I stand with your program and what I should focus on improving.

Thank you for your time, and I hope to speak with you soon.

Best regards,  
Noah Lach  
Midfielder/Forward | Class of 2028  
Sporting Kansas City Academy  
[Phone Number - leave blank for manual entry]  
noahlach@gmail.com  
Portfolio: https://slach80.github.io/nonotib

---

⚠️ **Note:** Placeholders in [brackets] need to be filled before sending!

---

## Bulk Email Process

### How Bulk Send Works

**Menu:** Coach Outreach → Send Bulk Emails (All Uncontacted)

```
1. Script scans ALL rows (2 to last row)
2. Identifies uncontacted coaches:
   - Has email? ✅
   - Date Contacted empty? ✅
3. Counts total: "Found 15 uncontacted coaches"
4. Checks daily limit (90 emails max)
5. Shows confirmation dialog
6. Loops through each school:
   - Generate email
   - Send via Gmail
   - Update sheet
   - Wait 500ms (rate limiting)
   - Continue to next school
7. Shows summary: "Sent 15 emails, 0 errors"
```

### Rate Limiting Protection

```javascript
// Max 90 emails per day (safety margin under Gmail's 100)
CONFIG.DAILY_EMAIL_LIMIT = 90

// If you try to send more:
if (uncontactedCount > 90) {
  alert: "Only first 90 will be sent. Run again tomorrow for the rest."
}

// Delay between sends (500ms = 0.5 seconds)
Utilities.sleep(500)
```

### Progress During Bulk Send

The script processes schools one at a time:
```
Row 2: ✅ Email sent to John Doe at Rockhurst
       (500ms delay)
Row 3: ✅ Email sent to Jane Smith at MidAmerica Nazarene
       (500ms delay)
Row 4: ⚠️  Skipped - already contacted on 05/01/2026
       (no delay)
Row 5: ❌ Error - invalid email address (logged to Notes)
       (500ms delay)
Row 6: ✅ Email sent to Bob Wilson at Park University
       ...and so on
```

---

## Configuration You Need to Update

Before sending ANY emails, update these in `CoachOutreachCRM.gs`:

### Line 22 - SportsRecruits URL
```javascript
SPORTSRECRUITS_URL: '[YOUR_SPORTSRECRUITS_PROFILE_URL]',
```
**Change to:** Noah's actual SportsRecruits profile link

### Lines 214-218 - Placeholders
```javascript
const placeholders = {
  specificReason: '[specific reason]',        // ← Leave as placeholder (personalize per coach)
  achievement: 'competed at MLS Next...',     // ← Already filled (can customize)
  gpa: '[GPA]',                               // ← Update to actual GPA
  satYear: '[Year]',                          // ← Update to SAT test year (e.g., "2026")
  phoneNumber: '[Phone Number]'               // ← Update to Noah's phone
}
```

**Recommended approach:**
- Fill `gpa`, `satYear`, `phoneNumber` in the script → applies to ALL emails
- Leave `specificReason` as placeholder → personalize manually before sending each email

---

## Personalization Strategy

### What MUST Be Personalized

**[specific reason]** — Why Noah is interested in THAT school specifically

Examples:
```
Bad (generic):
"I am interested in your program because it has a great reputation."

Good (specific):
"I am interested in your program because of your team's recent SSC Championship 
and the strong academic programs in sports management."

Better (shows research):
"I am interested in your program because of Coach Doe's development of midfielders 
like [former player name] and Rockhurst's direct pathway to graduate programs."
```

### How to Personalize at Scale

**Option 1: Personalize in Sheet Before Bulk Send**
- Add a column: "Why This School"
- Fill in 2-3 sentences per school
- Manually copy/paste into each sent email after the fact ❌ (not efficient)

**Option 2: Send Individually with Custom Edits**
- Send one at a time
- Edit the `[specific reason]` placeholder in the script before each send
- Time-consuming but most personalized ✅

**Option 3: Tiered Approach**
- HIGH priority schools (15-20): Full personalization, send individually
- MEDIUM priority (10): Light personalization, bulk send with general reason
- BACKUP schools: Use default template

---

## Safety Features Built In

### 1. Duplicate Prevention
```javascript
// Won't send if Date Contacted is filled
if (dateContacted) {
  return error: 'Coach already contacted on MM/DD/YYYY'
}
```

### 2. Placeholder Warnings
```javascript
// Detects [brackets] in email body
if (emailBody.includes('[')) {
  // Sends email anyway (gives you flexibility)
  // But logs warning in Notes column
  addNote: "WARNING: Email sent with unfilled placeholders..."
}
```

### 3. Gmail Quota Protection
```javascript
// Stops at 90 emails per day
if (sentCount >= CONFIG.DAILY_EMAIL_LIMIT) {
  break; // Stop sending
}
```

### 4. Error Logging
```javascript
try {
  GmailApp.sendEmail(...)
} catch (error) {
  // Doesn't crash the script
  // Logs error to Notes column
  // Continues with next school
  addNote: "Email send failed: [error message]"
}
```

---

## Test Before You Blast

### Step 1: Test Email Template

**Menu:** Coach Outreach → Test Email Template

```javascript
// Sends to noahlach@gmail.com (yourself)
// Uses Row 2 data (first school)
// Shows you exactly what coaches will receive
```

**Check in your inbox:**
- ✅ Subject line looks good?
- ✅ Greeting uses coach's last name correctly?
- ✅ Links work (portfolio + SportsRecruits)?
- ✅ Placeholders clearly visible?
- ✅ HTML formatting displays properly?
- ✅ Mobile formatting looks good?

### Step 2: Send to ONE Real Coach

Pick a lower-priority school first:
- Send to one coach
- Wait for reply (or no reply after 1 week)
- Review what worked / didn't work
- Adjust template if needed

### Step 3: Send First Small Batch

- Start with 5-10 schools
- Track response rate
- Iterate on personalization
- Then scale up to bulk sends

---

## Tracking Responses

### When a Coach Replies

**Manually update the sheet:**

1. **Response Status** column → Change to:
   - "Replied - Interested"
   - "Replied - Not Recruiting Class 2028"
   - "Replied - Will Follow Up"
   - "No Response"

2. **Notes** column → Add details:
   ```
   [05/15/2026] Coach replied: Interested in seeing game film.
   Asked about upcoming showcases. Follow up with MLS Next Cup highlights.
   ```

### Weekly Digest

**Menu:** Coach Outreach → Generate Weekly Digest

Gets you a summary:
- Total contacted: 25 schools
- Responses received: 8 (32% response rate)
- Awaiting response: 17
- Follow-ups needed: 5 schools (no reply in 2+ weeks)
- This week's activity: 10 new emails sent

---

## Common Issues & Solutions

### "Authorization required" error
**Cause:** First time running the script  
**Solution:** Follow Step 5 in COACH_CRM_SETUP.md to authorize Gmail/Sheets access

### "No email address found"
**Cause:** Coach Email column is empty  
**Solution:** Research and fill in coach email before sending

### "Coach already contacted"
**Cause:** Date Contacted column has a date (duplicate prevention)  
**Solution:** This is intentional! Clear the date ONLY if you really want to re-send

### Email sent but has [brackets]
**Cause:** Placeholders not filled (GPA, Year, Phone, specific reason)  
**Solution:** Check Notes column for warning, update CONFIG or personalize per school

### Only 90 emails sent (have 100+ schools)
**Cause:** Daily Gmail limit (safety margin)  
**Solution:** Run bulk send again tomorrow to send the next batch

---

## Best Practices

1. **Test first** — Always send test email to yourself before bulk sending
2. **Personalize HIGH priority** — Top 15-20 schools deserve custom [specific reason]
3. **Follow up** — No reply after 3-4 weeks? Send update with new highlights
4. **Track responses immediately** — Update Response Status when coaches reply
5. **Don't spam** — One email, then wait 3-4 weeks before follow-up
6. **Keep Notes current** — Log everything: replies, camp invites, phone calls
7. **Spread out bulk sends** — 10-20 per day is less spammy than 90 at once

---

## The Email Script Files

| File | Purpose |
|------|---------|
| `CoachOutreachCRM.gs` | Google Apps Script code (paste into Extensions → Apps Script) |
| `COACH_CRM_SETUP.md` | Full setup guide (how to install + configure) |
| `EMAIL_PROCESS_WALKTHROUGH.md` | This document (how emails work) |
| `coach_crm_data.csv` | Import file for Google Sheets (generated by Python script) |

---

**Questions?** Read the setup guide first, then test with the Test Email Template function!

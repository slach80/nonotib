# TODO

## ~~Gmail Automation CRM — Coach Outreach~~ ✅ COMPLETE (May 7-8, 2026)
~~Build a Google Apps Script + Sheets CRM for tracking and automating coach email outreach~~
- ✅ Google Sheet CRM structure with coach contacts, roster window scores
- ✅ Apps Script (`CoachOutreachCRM.gs`) for automated email sending
- ✅ Python export script (`monitor/export_crm_data.py`) generates CSV from SCHOOLS data
- ✅ Coach contact research completed (13 of 19 schools have complete contacts)
- ✅ Email template implemented with personalization placeholders
- ✅ Setup guide (`COACH_CRM_SETUP.md`) and process walkthrough (`EMAIL_PROCESS_WALKTHROUGH.md`)
- ✅ Ready to import CSV and begin outreach

**Next Steps:**
1. Fill in missing coach contacts (6 schools need manual research: UMKC, Tampa, USF, SDSU, SD Christian)
2. Import `coach_crm_data.csv` to Google Sheets
3. Install Apps Script and configure (update SportsRecruits URL, GPA, phone placeholders)
4. Begin targeted outreach starting with HIGH roster window schools

## Security / Access Control
- `index.html` = public; all other pages need protection
- Key decisions still open:
  - Hosting: GitHub Pages vs. Netlify (Netlify recommended for server-side auth)
  - Access model: single shared password vs. per-person links/tokens
  - Audience: family only, or coaches too? Same access level or different?
- Leading option: Netlify host-level password protection (free, true server-side, no code changes)

## ~~Coach Contact Research~~ ✅ COMPLETE (May 7-8, 2026)
~~Research and add direct coach emails/phones for schools~~
- ✅ **KC/MO:** 5 complete (Evangel, William Jewell, Southwest Baptist, Truman State, Missouri State)
  - ⚠️ UMKC needs manual check (JavaScript site)
  - ❌ Missouri Western State removed (no men's soccer program)
- ✅ **Tampa Bay:** 5 complete (Southeastern, Saint Leo, Warner, Eckerd, Lynn)
  - ⚠️ USF partial (general email only)
  - ⚠️ Tampa Cloudflare blocked (call 813-257-3100)
- ✅ **California:** 3 complete (Cal State East Bay, USD, SJSU)
  - ⚠️ SDSU partial (general email)
  - ⚠️ SD Christian needs phone call

**Results:** 13 of 19 schools (68%) have complete contacts. See `COACH_CONTACTS_RESEARCH.md`

## JUCO Research — Reference Only
- ✅ **Kansas City Area:** 3 programs identified (JCCC, KCKCC, Neosho County CC)
- ✅ **Tampa Bay Area:** Zero local programs (archived research)
- ✅ **Decision:** Keep as reference only, not adding to active recruiting targets
- **Rationale:** Noah is college prep track, MLS Next background = 4-year ready, JUCOs below his trajectory
- **Documentation:** `KC_JUCO_RESEARCH.md`, `FLORIDA_JUCO_RESEARCH.md`

## International Recruiting — Japan Research
- ✅ **MEXT Scholarship:** Full funding research complete (¥117K/month + tuition + flights)
- ✅ **Target Universities:** Waseda, Tsukuba, Sophia identified with English programs
- ✅ **Competition Level:** NCAA D1 equivalent, strong J-League pathway
- ✅ **Timeline:** Application May 2027, decision early 2028
- ✅ **Recommendation:** Keep as backup while pursuing US recruiting
- ✅ **Page Created:** `international.html` with comprehensive Japan section
- ✅ **Documentation:** `JAPAN_RECRUITING_RESEARCH.md` (450+ lines)
- 📅 **Reminder Set:** January 5, 2027 to review MEXT application timeline

## Family Website (future project)
- Two boys: Noah and Isaac — each with a public profile + private personal pages
- Shared pages TBD
- Hosting: AWS (future), custom domain pending; Netlify as interim bridge
- Structure: `noah.domain.com` / `isaac.domain.com` — roll nonotib content into Noah's section
- **Noah pages:** profile (public), college analysis, college map, scholarships, camps, test prep
- **Isaac pages:** profile (public), piano/music, college map (same recruiting concept as Noah), test prep, more TBD
- Security model ties into access control item above
- Design/structure — plan before building

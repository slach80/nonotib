# Dev-Prod Pipeline Setup

**Created:** May 9, 2026  
**Status:** Ready for GitHub token setup

---

## Overview

Automated pipeline that syncs `index.html` (hero page) from **nonotib** (dev) to **noahlach** (prod).

### Repositories

| Environment | Repo | URL | Purpose |
|-------------|------|-----|---------|
| **DEV** | `nonotib` | https://slach80.github.io/nonotib/ | Full recruiting site (family access) |
| **PROD** | `noahlach` | https://slach80.github.io/noahlach/ | Public hero page only (coaches) |

### Key Differences: Dev vs Prod

| Feature | Dev (nonotib) | Prod (noahlach) |
|---------|---------------|-----------------|
| **Pages** | index, colleges, map, scholarships, camps, testprep, international | **index.html only** |
| **Jersey #** | #21 | #16 |
| **Navigation** | Full dropdown (Noah + Recruiting) | Simplified (Profile, Journey, Highlights, Academics, References) |
| **Audience** | Family | Coaches (public) |

---

## How It Works

### Automatic Sync (GitHub Actions)

1. You commit/push changes to `nonotib/index.html`
2. GitHub Action detects the change
3. Action transforms `index.html`:
   - Changes jersey #21 → #16
   - Removes "Recruiting" dropdown from nav
   - Removes recruiting links from mobile menu
   - Removes "View College Analysis" link
4. Action pushes transformed `index.html` to `noahlach`
5. GitHub Pages auto-deploys prod site

### Manual Sync (when needed)

Run from `nonotib` directory:
```bash
./sync-to-prod.sh
```

Use this if:
- GitHub Actions is down
- You want to sync without committing
- You need to test the sync process

### Rollback (if something breaks)

From either repo directory:
```bash
./rollback-prod.sh 1    # rollback 1 commit
./rollback-prod.sh 3    # rollback 3 commits
```

Interactive prompts confirm before force-pushing.

---

## Setup Instructions

### 1. Create GitHub Personal Access Token (PAT)

The GitHub Action needs permission to push to `noahlach` repo.

**Steps:**
1. Go to GitHub: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Name: `PROD_SYNC_TOKEN`
4. Expiration: **No expiration** (or 1 year if you prefer)
5. Scopes: Check **`repo`** (full control of private repositories)
6. Click **"Generate token"**
7. **Copy the token** (you won't see it again!)

### 2. Add Token to nonotib Repository Secrets

1. Go to: https://github.com/slach80/nonotib/settings/secrets/actions
2. Click **"New repository secret"**
3. Name: `PROD_SYNC_TOKEN`
4. Value: *paste the token from step 1*
5. Click **"Add secret"**

### 3. Test the Pipeline

**Option A: Commit a test change**
```bash
cd /home/slach/Projects/nonotib
echo "<!-- Test sync -->" >> index.html
git add index.html .github/workflows/sync-to-prod.yml
git commit -m "Setup dev-prod pipeline"
git push origin main
```

Then watch the GitHub Action run:
- https://github.com/slach80/nonotib/actions

**Option B: Manual sync first**
```bash
cd /home/slach/Projects/nonotib
./sync-to-prod.sh
```

Check prod site: https://slach80.github.io/noahlach/

---

## Workflow

### Normal Development

```bash
cd /home/slach/Projects/nonotib

# Make changes to any page
vim index.html        # Changes will auto-sync to prod
vim colleges.html     # Changes stay in dev only

# Commit and push
git add .
git commit -m "Update hero stats"
git push origin main

# GitHub Action automatically syncs index.html to prod
# Check: https://slach80.github.io/noahlach/
```

### If Something Breaks

**Quick rollback:**
```bash
cd /home/slach/Projects/noahlach
./rollback-prod.sh 1
```

**Then fix dev and re-sync:**
```bash
cd /home/slach/Projects/nonotib
# Fix the issue
git add index.html
git commit -m "Fix: correct coach contact"
git push origin main
# Action will auto-sync the fix
```

---

## File Locations

### Dev Repo (`nonotib`)
```
/home/slach/Projects/nonotib/
├── .github/workflows/sync-to-prod.yml  ← GitHub Action
├── sync-to-prod.sh                     ← Manual sync script
├── rollback-prod.sh                    ← Rollback script
├── index.html                          ← Hero page (syncs to prod)
├── colleges.html                       ← Dev only
├── map.html                            ← Dev only
├── scholarships.html                   ← Dev only
├── camps.html                          ← Dev only
├── testprep.html                       ← Dev only
└── international.html                  ← Dev only
```

### Prod Repo (`noahlach`)
```
/home/slach/Projects/noahlach/
├── rollback-prod.sh    ← Rollback script
├── index.html          ← Auto-synced from dev
└── README.md
```

---

## Troubleshooting

### Action fails with "Permission denied"
- Check `PROD_SYNC_TOKEN` secret exists in nonotib repo
- Verify token has `repo` scope
- Token may have expired (regenerate)

### Changes not appearing on prod
1. Check GitHub Action ran successfully: https://github.com/slach80/nonotib/actions
2. Check GitHub Pages deployment status: https://github.com/slach80/noahlach/deployments
3. Clear browser cache (Ctrl+Shift+R)

### Want to manually sync without committing
```bash
cd /home/slach/Projects/nonotib
./sync-to-prod.sh
```

### Need to stop auto-sync temporarily
Rename the workflow file:
```bash
cd /home/slach/Projects/nonotib
mv .github/workflows/sync-to-prod.yml .github/workflows/sync-to-prod.yml.disabled
git add .github/workflows/
git commit -m "Temporarily disable auto-sync"
git push
```

Re-enable by renaming back:
```bash
mv .github/workflows/sync-to-prod.yml.disabled .github/workflows/sync-to-prod.yml
```

---

## Testing Checklist

Before going live, verify:

- [ ] GitHub token created and added to secrets
- [ ] Manual sync works: `./sync-to-prod.sh`
- [ ] Prod site shows #16 (not #21)
- [ ] Prod nav has no "Recruiting" dropdown
- [ ] Prod mobile menu has no recruiting links
- [ ] All external links work (YouTube, Instagram, Taka.io, emails)
- [ ] GitHub Action runs successfully on push
- [ ] Rollback script works: `./rollback-prod.sh 1`

---

## Future Enhancements

**Telegram Alerts (optional):**
Add to GitHub Action to get notified on sync success/failure:
```yaml
- name: Send Telegram notification
  if: always()
  run: |
    curl -X POST "https://api.telegram.org/bot${{ secrets.TELEGRAM_BOT_TOKEN }}/sendMessage" \
      -d "chat_id=${{ secrets.TELEGRAM_CHAT_ID }}" \
      -d "text=Prod sync ${{ job.status }}: ${{ github.event.head_commit.message }}"
```

**Preview Before Push:**
Add approval step to GitHub Action (requires manual approval in GitHub UI before pushing to prod).

---

**Last Updated:** May 9, 2026  
**Maintainer:** slach  
**Related:** `TODO.md`, `CLAUDE.md`

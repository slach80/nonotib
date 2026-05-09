#!/bin/bash
# Manual sync script: sync index.html from nonotib (dev) to noahlach (prod)
# Usage: ./sync-to-prod.sh

set -e

DEV_REPO="/home/slach/Projects/nonotib"
PROD_REPO="/home/slach/Projects/noahlach"

echo "🔄 Starting manual sync from dev to prod..."

# Check if both repos exist
if [ ! -d "$DEV_REPO" ]; then
  echo "❌ Dev repo not found: $DEV_REPO"
  exit 1
fi

if [ ! -d "$PROD_REPO" ]; then
  echo "❌ Prod repo not found: $PROD_REPO"
  exit 1
fi

# Copy index.html
echo "📄 Copying index.html..."
cp "$DEV_REPO/index.html" "$PROD_REPO/index.html"

cd "$PROD_REPO"

# Transform for production
echo "✏️  Transforming for production..."

# Change jersey number from #21 to #16
sed -i 's/hero-ghost-num">21</hero-ghost-num">16</g' index.html
sed -i 's/NL<span>16<\/span>/NL<span>16<\/span>/g' index.html

# Remove "Recruiting" dropdown navigation
sed -i '/<li class="nav-dropdown">/,/<\/li>/{
  /<a href="colleges.html">Recruiting<\/a>/,/<\/div>/d
}' index.html

# Remove recruiting links from mobile menu
sed -i '/<span class="mob-group-label">Recruiting<\/span>/,/<span class="mob-group-label">Connect<\/span>/{
  /<span class="mob-group-label">Recruiting<\/span>/d
  /<a href="colleges.html">/d
  /<a href="map.html">/d
  /<a href="scholarships.html">/d
  /<a href="camps.html">/d
  /<a href="testprep.html">/d
  /<a href="international.html">/d
}' index.html

# Remove "View In-Depth College Analysis" link
sed -i '/<a href="colleges.html" class="colleges-link/d' index.html

# Simplify nav to remove dropdown functionality
sed -i 's|<li class="nav-dropdown">|<li>|g' index.html
sed -i 's|<a href="index.html">Noah</a>|<a href="#stats">Profile</a></li><li><a href="#journey">Journey</a></li><li><a href="#highlights">Highlights</a></li><li><a href="#academics">Academics</a></li><li><a href="#references">References</a>|g' index.html
sed -i '/<div class="nav-dropdown-menu">/,/<\/div>/d' index.html

# Git operations
echo "📦 Committing changes..."
git add index.html

if git diff --cached --quiet; then
  echo "ℹ️  No changes to commit"
else
  LAST_DEV_COMMIT=$(cd "$DEV_REPO" && git log -1 --oneline)
  git commit -m "Manual sync from dev: $LAST_DEV_COMMIT"
  echo "✅ Committed to local prod repo"

  echo "🚀 Pushing to GitHub..."
  git push origin main
  echo "✅ Successfully synced to production!"
fi

echo ""
echo "🎉 Sync complete!"
echo "   Dev: https://slach80.github.io/nonotib/"
echo "   Prod: https://slach80.github.io/noahlach/"

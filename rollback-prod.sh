#!/bin/bash
# Rollback production to previous commit
# Usage: ./rollback-prod.sh [number_of_commits]
# Example: ./rollback-prod.sh 1  (rollback 1 commit)

set -e

PROD_REPO="/home/slach/Projects/noahlach"
ROLLBACK_COUNT="${1:-1}"

echo "⚠️  ROLLBACK: Going back $ROLLBACK_COUNT commit(s) in production"

if [ ! -d "$PROD_REPO" ]; then
  echo "❌ Prod repo not found: $PROD_REPO"
  exit 1
fi

cd "$PROD_REPO"

# Show current status
echo ""
echo "📋 Current production commits (last 5):"
git log --oneline -5
echo ""

# Confirm rollback
read -p "🔴 Are you sure you want to rollback $ROLLBACK_COUNT commit(s)? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "❌ Rollback cancelled"
  exit 0
fi

# Perform rollback
echo "🔄 Rolling back..."
git reset --hard HEAD~$ROLLBACK_COUNT

echo "✅ Local rollback complete. Showing current state:"
git log --oneline -3

echo ""
read -p "🚀 Push rollback to GitHub? This will force-update production. (yes/no): " PUSH_CONFIRM

if [ "$PUSH_CONFIRM" != "yes" ]; then
  echo "ℹ️  Rollback applied locally only. Run 'git push origin main --force' manually to update production."
  exit 0
fi

# Force push to remote
echo "🚀 Force-pushing to production..."
git push origin main --force

echo ""
echo "✅ Production rolled back successfully!"
echo "   Prod URL: https://slach80.github.io/noahlach/"
echo ""
echo "💡 To re-sync latest dev version, run: ./sync-to-prod.sh"

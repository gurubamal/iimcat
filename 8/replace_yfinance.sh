#!/bin/bash
# Replace yfinance with yfinance_replacement across all key files

echo "========================================="
echo "REPLACING YFINANCE WITH WEB SCRAPING"
echo "========================================="
echo ""

# Backup original files
echo "Creating backups..."
mkdir -p .yfinance_backup
for file in realtime_price_fetcher.py fundamental_data_fetcher.py technical_scoring_wrapper.py; do
    if [ -f "$file" ]; then
        cp "$file" ".yfinance_backup/${file}.bak"
        echo "  ✅ Backed up: $file"
    fi
done
echo ""

# Replace import statements
echo "Replacing import statements..."

# Pattern 1: import yfinance as yf
sed -i 's/import yfinance as yf/import yfinance_replacement as yf/g' realtime_price_fetcher.py
sed -i 's/import yfinance as yf/import yfinance_replacement as yf/g' fundamental_data_fetcher.py
sed -i 's/import yfinance as yf/import yfinance_replacement as yf/g' technical_scoring_wrapper.py

# Pattern 2: import yfinance
sed -i 's/^import yfinance$/import yfinance_replacement as yfinance/g' realtime_price_fetcher.py
sed -i 's/^import yfinance$/import yfinance_replacement as yfinance/g' fundamental_data_fetcher.py
sed -i 's/^import yfinance$/import yfinance_replacement as yfinance/g' technical_scoring_wrapper.py

# Pattern 3: from yfinance import
sed -i 's/from yfinance import/from yfinance_replacement import/g' realtime_price_fetcher.py
sed -i 's/from yfinance import/from yfinance_replacement import/g' fundamental_data_fetcher.py
sed -i 's/from yfinance import/from yfinance_replacement import/g' technical_scoring_wrapper.py

echo "  ✅ realtime_price_fetcher.py"
echo "  ✅ fundamental_data_fetcher.py"
echo "  ✅ technical_scoring_wrapper.py"
echo ""

# Add warning comments
echo "Adding warning comments..."
for file in realtime_price_fetcher.py fundamental_data_fetcher.py technical_scoring_wrapper.py; do
    if [ -f "$file" ]; then
        # Add comment at top (after shebang and docstring)
        sed -i '3i\# ⚠️  WARNING: Using yfinance_replacement (web scraping) instead of yfinance\n# This uses Screener.in data which may be 3 YEARS OUTDATED!\n' "$file"
    fi
done
echo "  ✅ Added warnings"
echo ""

echo "========================================="
echo "✅ REPLACEMENT COMPLETE"
echo "========================================="
echo ""
echo "Changes made:"
echo "  1. Replaced 'import yfinance' with 'import yfinance_replacement'"
echo "  2. Added warning comments about data freshness"
echo "  3. Created backups in .yfinance_backup/"
echo ""
echo "To revert:"
echo "  cp .yfinance_backup/*.bak ."
echo ""
echo "⚠️  IMPORTANT:"
echo "  - Screener.in data is 3 YEARS OLD (Sep 2022)"
echo "  - This will give OPPOSITE trading signals for some stocks"
echo "  - Use at your own risk!"
echo ""

#!/usr/bin/env bash
# packages.sh — Install Firefox on WSL2 (Ubuntu 20.04 / 22.04 / 24.04)
# Run once:  bash packages.sh

set -euo pipefail

echo ">>> Updating apt cache…"
sudo apt-get update -q

# ── Install Firefox via Mozilla Team PPA (works on all Ubuntu versions) ───────
# Ubuntu 22.04+ only ships Firefox as a snap; this gets a real deb instead.
if ! command -v firefox &>/dev/null; then
    echo ">>> Adding Mozilla Team PPA…"
    sudo apt-get install -y -q software-properties-common
    sudo add-apt-repository -y ppa:mozillateam/ppa

    # Make PPA take priority over snap redirect
    sudo tee /etc/apt/preferences.d/mozilla-firefox > /dev/null << 'PREF'
Package: *
Pin: release o=LP-PPA-mozillateam
Pin-Priority: 1001
PREF

    sudo apt-get update -q
    sudo apt-get install -y -q firefox
else
    echo ">>> Firefox already installed, skipping."
fi

echo ">>> Firefox version:"
firefox --version

# ── geckodriver: downloaded automatically by seleniumbase on first run ────────
echo ">>> Installing Python packages…"
pip install -r requirements.txt

echo ">>> Pre-fetching geckodriver via seleniumbase…"
python -c "
from seleniumbase.core import download_helper
download_helper.download_driver(driver='geckodriver')
print('geckodriver OK.')
"

echo ""
echo "✅ Done!  Run:  streamlit run app.py"
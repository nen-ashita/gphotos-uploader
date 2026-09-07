#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== Google Photos Uploader Setup ==="
echo "Project directory: $DIR"

# 1. Virtual Environment & Dependencies
if [ ! -d "$DIR/venv" ]; then
    echo "[1/4] Creating Python virtual environment..."
    python3 -m venv "$DIR/venv"
fi

echo "[2/4] Installing Python dependencies..."
"$DIR/venv/bin/pip" install --quiet --upgrade pip
"$DIR/venv/bin/pip" install --quiet -r "$DIR/requirements.txt"

# 2. CLI Symlink
echo "[3/4] Setting up CLI symlink (gphotos-upload)..."
mkdir -p "$HOME/.local/bin"
ln -sf "$DIR/bin/gphotos-upload" "$HOME/.local/bin/gphotos-upload"

# 3. macOS App & Quick Action
echo "[4/4] Installing Finder Quick Action & compiling macOS App..."
mkdir -p "$HOME/Library/Services"
cp -R "$DIR/Upload to Google Photos.workflow" "$HOME/Library/Services/"

osacompile -o "$DIR/Upload to Google Photos.app" "$DIR/droplet.applescript"

echo ""
echo "=== Setup Completed Successfully ==="
"$DIR/bin/gphotos-upload" --status
echo ""
echo "Next Steps:"
echo "1. Place your 'credentials.json' from Google Cloud Console in:"
echo "   $DIR/credentials.json  (or ~/.config/gphotos-uploader/credentials.json)"
echo "2. Run 'gphotos-upload --auth' in terminal to log in via browser once."
echo "3. Right-click any photo/video in Finder > Quick Actions > 'Upload to Google Photos' to upload!"

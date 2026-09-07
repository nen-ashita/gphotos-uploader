# Google Photos Uploader for macOS

**English** | [日本語 (Japanese)](README.ja.md)

A seamless macOS tool to upload photos and videos directly to Google Photos in **original quality**.
Supports Finder Right-Click (Quick Action), Drag-and-Drop App, and Terminal CLI.

---

## 3 Ways to Use

### 1. Finder Quick Action (Right-Click Context Menu)
1. Select photos, videos, or folders in Finder.
2. Right-click > **Quick Actions** > **Upload to Google Photos**.
3. Files upload in background with macOS notification upon completion.

### 2. Drag & Drop App (`Upload to Google Photos.app`)
- Simply drag and drop photos or folders onto the app icon.
- Double-clicking the app opens a file chooser dialog or status/auth checker.
- Can be placed on your Desktop, Dock, or `/Applications`.

### 3. Terminal Command (`gphotos-upload`)
```bash
# Upload one or more files
gphotos-upload photo1.jpg photo2.heic

# Upload directory recursively
gphotos-upload ~/Pictures/Vacation/

# Upload to a specific album (creates album if not existing)
gphotos-upload --album "Summer 2026" photo.jpg

# Send macOS notification on completion
gphotos-upload --notify photo.jpg

# Check authentication & configuration status
gphotos-upload --status
```

---

## Supported Media Formats (Original Quality Preserved)

- **Images**: JPEG (`.jpg`, `.jpeg`), PNG (`.png`), HEIC/HEIF (`.heic`, `.heif`), WebP (`.webp`), GIF (`.gif`), TIFF (`.tif`, `.tiff`), BMP (`.bmp`), RAW (`.dng`, `.cr2`, `.nef`, `.arw`, `.rw2`)
- **Videos**: MP4 (`.mp4`), MOV (`.mov`), M4V (`.m4v`), AVI (`.avi`), MKV (`.mkv`), MPEG (`.mpg`, `.mpeg`)

---

## Quick Setup Guide

This tool uses the official Google Photos Library API with the `photoslibrary.appendonly` scope to securely upload media.
Because Google requires OAuth 2.0 user credentials, you need to create a free OAuth client ID in your Google Cloud Console once.

### Step 1: Create OAuth Client in Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a project (e.g., `gphotos-uploader`).
2. Navigate to **APIs & Services > Library**, search for **Photos Library API**, and click **Enable**.
3. Go to **APIs & Services > OAuth consent screen**:
   - User Type: **External** > Create
   - Fill in App Name (e.g., `gphotos-uploader`) and your email address.
   - On the **Test users** page, click **Add Users** and add your Google account email (Essential: only test users can log in while in testing mode).
4. Go to **APIs & Services > Credentials > Create Credentials > OAuth client ID**:
   - Application type: **Desktop App**
   - Name: `gphotos-uploader-mac`
   - Click **Create**.
5. Download the client secret JSON file.
6. Rename the downloaded file to `credentials.json` and place it in:
   - `credentials.json` (in this repository directory)
   - OR `~/.config/gphotos-uploader/credentials.json`

### Step 2: Run Setup Script
```bash
./setup_macos.sh
```
This automatically sets up Python virtual environment, compiles the macOS App, installs the Finder Quick Action (`~/Library/Services/`), and creates the `gphotos-upload` command symlink.

### Step 3: Authenticate
Run in terminal:
```bash
gphotos-upload --auth
```
- A browser window will open asking you to sign in with your Google account.
- If warned "Google hasn't verified this app", click **Advanced > Go to gphotos-uploader (unsafe)** to continue (safe because you are using your own private GCP project).
- Once authenticated, tokens are safely saved to `~/.config/gphotos-uploader/token.json` (chmod 600) and automatically refreshed.

---

## License

MIT License

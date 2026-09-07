import os
import sys
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import requests
from google.oauth2.credentials import Credentials

UPLOAD_URL = "https://photoslibrary.googleapis.com/v1/uploads"
BATCH_CREATE_URL = "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate"
ALBUMS_URL = "https://photoslibrary.googleapis.com/v1/albums"

SUPPORTED_IMAGE_EXTS = {
    ".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif",
    ".gif", ".tif", ".tiff", ".bmp", ".dng", ".cr2", ".nef", ".arw", ".rw2"
}

SUPPORTED_VIDEO_EXTS = {
    ".mp4", ".mov", ".m4v", ".avi", ".mkv", ".mpg", ".mpeg", ".wmv"
}

SUPPORTED_EXTS = SUPPORTED_IMAGE_EXTS | SUPPORTED_VIDEO_EXTS

def get_mime_type(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    if ext in (".heic", ".heif"):
        return "image/heic"
    if ext == ".dng":
        return "image/x-adobe-dng"
    
    mime, _ = mimetypes.guess_type(str(file_path))
    return mime or "application/octet-stream"

def is_supported_media(file_path: Path) -> bool:
    return file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTS

def collect_files(targets: List[str]) -> List[Path]:
    """指定されたファイルやディレクトリから対象メディアファイルを再帰的に収集します"""
    files: List[Path] = []
    for target in targets:
        p = Path(target).expanduser().resolve()
        if p.is_file():
            if is_supported_media(p):
                files.append(p)
            else:
                print(f"スキップ（非対応形式）: {p.name}", file=sys.stderr)
        elif p.is_dir():
            for item in p.rglob("*"):
                if is_supported_media(item):
                    files.append(item)
        else:
            print(f"スキップ（存在しないパス）: {target}", file=sys.stderr)
    
    # 重複を除去しつつ順序を維持
    seen = set()
    unique_files = []
    for f in files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)
    return unique_files

class GooglePhotosUploader:
    def __init__(self, credentials: Credentials):
        self.credentials = credentials

    def _get_auth_headers(self) -> Dict[str, str]:
        if not self.credentials.valid and self.credentials.refresh_token:
            from google.auth.transport.requests import Request
            self.credentials.refresh(Request())
        return {"Authorization": f"Bearer {self.credentials.token}"}

    def upload_raw_file(self, file_path: Path, progress_callback: Optional[Callable[[int, int], None]] = None) -> str:
        """ファイルをGoogle Photosにバイナリ送信して uploadToken を取得します"""
        mime_type = get_mime_type(file_path)
        file_size = file_path.stat().st_size
        
        headers = self._get_auth_headers()
        headers.update({
            "Content-Type": "application/octet-stream",
            "X-Goog-Upload-Content-Type": mime_type,
            "X-Goog-Upload-Protocol": "raw",
        })

        with open(file_path, "rb") as f:
            if progress_callback:
                class ProgressReader:
                    def __init__(self, fp, total, cb):
                        self.fp = fp
                        self.total = total
                        self.cb = cb
                        self.uploaded = 0

                    def read(self, size=-1):
                        chunk = self.fp.read(size)
                        if chunk:
                            self.uploaded += len(chunk)
                            self.cb(self.uploaded, self.total)
                        return chunk

                    def __len__(self):
                        return self.total

                data = ProgressReader(f, file_size, progress_callback)
            else:
                data = f

            res = requests.post(UPLOAD_URL, headers=headers, data=data)

        if res.status_code != 200:
            raise RuntimeError(f"アップロードトークン取得失敗 ({res.status_code}): {res.text}")

        return res.text.strip()

    def batch_create_media_items(
        self,
        items: List[Dict[str, str]],
        album_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        uploadToken からメディアアイテムを一括生成します。
        items: [{"file_name": str, "upload_token": str, "description": str (optional)}]
        """
        headers = self._get_auth_headers()
        headers["Content-Type"] = "application/json"

        new_media_items = []
        for it in items:
            new_media_items.append({
                "description": it.get("description", ""),
                "simpleMediaItem": {
                    "fileName": it["file_name"],
                    "uploadToken": it["upload_token"]
                }
            })

        payload = {"newMediaItems": new_media_items}
        if album_id:
            payload["albumId"] = album_id

        res = requests.post(BATCH_CREATE_URL, headers=headers, json=payload)
        if res.status_code != 200:
            raise RuntimeError(f"メディア作成API失敗 ({res.status_code}): {res.text}")

        data = res.json()
        return data.get("newMediaItemResults", [])

    def create_album(self, title: str) -> Dict[str, Any]:
        """新規アルバムを作成します"""
        headers = self._get_auth_headers()
        headers["Content-Type"] = "application/json"
        payload = {"album": {"title": title}}
        res = requests.post(ALBUMS_URL, headers=headers, json=payload)
        if res.status_code != 200:
            raise RuntimeError(f"アルバム作成失敗 ({res.status_code}): {res.text}")
        return res.json()

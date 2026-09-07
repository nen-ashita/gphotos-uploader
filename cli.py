import os
import sys
import time
import argparse
from pathlib import Path
from tqdm import tqdm

from auth import get_credentials, check_status, CredentialsNotFoundError
from uploader import GooglePhotosUploader, collect_files
from notify import send_notification

def main():
    parser = argparse.ArgumentParser(
        description="Upload photos and videos to Google Photos in original quality."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Path(s) to media files or directories to upload"
    )
    parser.add_argument(
        "--album",
        "-a",
        type=str,
        default=None,
        help="Target album name (creates new album if not exists)"
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Show macOS desktop notification on completion"
    )
    parser.add_argument(
        "--auth",
        action="store_true",
        help="Perform or verify OAuth authentication"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Display authentication and configuration status"
    )

    args = parser.parse_args()

    if args.status:
        st = check_status()
        print("=== Google Photos Uploader Status ===")
        print(f"Config Directory:     {st['config_dir']}")
        print(f"Credentials Found:    {'Yes' if st['credentials_configured'] else 'No (missing)'}")
        print(f"Token Saved:          {'Yes' if st['token_saved'] else 'No (not authenticated)'}")
        print(f"Token Status:         {'Valid' if st['token_valid'] else 'Invalid or expired'}")
        return

    if args.auth:
        try:
            get_credentials(interactive=True)
            print("Authentication successful.")
            if args.notify:
                send_notification("Google Photos", "Authentication completed successfully.")
        except Exception as e:
            print(f"Authentication error: {e}", file=sys.stderr)
            if args.notify:
                send_notification("Google Photos Auth Error", str(e))
            sys.exit(1)
        return

    if not args.paths:
        parser.print_help()
        sys.exit(0)

    # 1. Authenticate
    try:
        creds = get_credentials(interactive=True)
    except CredentialsNotFoundError as e:
        print(f"\n[Error] {e}\n", file=sys.stderr)
        if args.notify:
            send_notification("Google Photos Error", "credentials.json is missing.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[Auth Error] {e}\n", file=sys.stderr)
        if args.notify:
            send_notification("Google Photos Auth Error", str(e))
        sys.exit(1)

    # 2. Collect files
    files = collect_files(args.paths)
    if not files:
        print("No supported photos or videos found.")
        if args.notify:
            send_notification("Google Photos", "No supported media files found.")
        return

    total_files = len(files)
    print(f"\nFound {total_files} media file(s) to upload.")
    if args.notify:
        send_notification("Google Photos Upload", f"Starting upload for {total_files} item(s)...")

    uploader = GooglePhotosUploader(creds)

    # Prepare album if requested
    album_id = None
    if args.album:
        try:
            print(f"Preparing album '{args.album}'...")
            alb_res = uploader.create_album(args.album)
            album_id = alb_res.get("id")
            print(f"Album ready (ID: {album_id})")
        except Exception as e:
            print(f"Warning: Failed to create album '{args.album}' ({e}). Uploading to library.", file=sys.stderr)

    # 3. Upload files
    start_time = time.time()
    success_count = 0
    failed_files = []
    BATCH_SIZE = 50
    
    with tqdm(total=total_files, desc="Uploading", unit="file") as pbar:
        tokens_batch = []
        for file_path in files:
            pbar.set_postfix_str(file_path.name[:25])
            try:
                upload_token = uploader.upload_raw_file(file_path)
                tokens_batch.append({
                    "file_name": file_path.name,
                    "upload_token": upload_token,
                    "path": file_path
                })
            except Exception as e:
                failed_files.append((file_path.name, str(e)))
                print(f"\nUpload failed ({file_path.name}): {e}", file=sys.stderr)
            
            if len(tokens_batch) >= BATCH_SIZE:
                success_count += _commit_batch(uploader, tokens_batch, album_id, failed_files)
                tokens_batch = []
            
            pbar.update(1)

        if tokens_batch:
            success_count += _commit_batch(uploader, tokens_batch, album_id, failed_files)

    elapsed = time.time() - start_time
    print("\n" + "=" * 40)
    print(f"Done! Succeeded: {success_count} / Failed: {len(failed_files)} ({elapsed:.1f}s)")
    if failed_files:
        print("\nFailed files:")
        for fname, err in failed_files:
            print(f"  - {fname}: {err}")
    print("=" * 40)

    if args.notify:
        if len(failed_files) == 0:
            send_notification(
                "Google Photos Upload Complete",
                f"Successfully uploaded {success_count} media file(s).",
                subtitle=f"Elapsed: {elapsed:.1f}s"
            )
        else:
            send_notification(
                "Google Photos Upload (With Errors)",
                f"Succeeded: {success_count} / Failed: {len(failed_files)}",
                subtitle=f"Elapsed: {elapsed:.1f}s"
            )

def _commit_batch(uploader, items, album_id, failed_files) -> int:
    batch_items = [{"file_name": it["file_name"], "upload_token": it["upload_token"]} for it in items]
    try:
        results = uploader.batch_create_media_items(batch_items, album_id=album_id)
        succeeded = 0
        for i, res in enumerate(results):
            status = res.get("status", {})
            code = status.get("code", 0)
            msg = status.get("message", "")
            if code == 0 or msg == "Success" or not msg:
                succeeded += 1
            else:
                failed_files.append((items[i]["file_name"], f"{code}: {msg}"))
        return succeeded
    except Exception as e:
        for it in items:
            failed_files.append((it["file_name"], f"batchCreate error: {e}"))
        return 0

if __name__ == "__main__":
    main()

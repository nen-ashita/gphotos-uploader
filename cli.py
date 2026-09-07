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
        description="Googleフォトに画像・動画をオリジナル画質のままアップロードするツール"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="アップロード対象の画像・動画ファイルまたはディレクトリパス"
    )
    parser.add_argument(
        "--album",
        "-a",
        type=str,
        default=None,
        help="アップロード先アルバム名（指定しない場合はメインライブラリ）"
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="完了時・エラー時にmacOSデスクトップ通知を送信する"
    )
    parser.add_argument(
        "--auth",
        action="store_true",
        help="OAuth認証の確認および実行のみを行います"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="認証・設定のステータスを表示します"
    )

    args = parser.parse_args()

    if args.status:
        st = check_status()
        print("=== Google Photos Uploader ステータス ===")
        print(f"設定ディレクトリ: {st['config_dir']}")
        print(f"credentials.json 存在: {'はい' if st['credentials_configured'] else 'いいえ (未設定)'}")
        print(f"token.json 存在: {'はい' if st['token_saved'] else 'いいえ (未認証)'}")
        print(f"トークン有効状態: {'有効' if st['token_valid'] else '無効または未取得'}")
        return

    if args.auth:
        try:
            get_credentials(interactive=True)
            print("認証に成功しました。")
            if args.notify:
                send_notification("Googleフォト認証", "認証が完了しました。")
        except Exception as e:
            print(f"認証エラー: {e}", file=sys.stderr)
            if args.notify:
                send_notification("Googleフォト認証エラー", str(e))
            sys.exit(1)
        return

    if not args.paths:
        parser.print_help()
        sys.exit(0)

    # 1. 認証情報の取得
    try:
        creds = get_credentials(interactive=True)
    except CredentialsNotFoundError as e:
        print(f"\n[エラー] {e}\n", file=sys.stderr)
        if args.notify:
            send_notification("Googleフォト エラー", "credentials.json が未設定です。")
        sys.exit(1)
    except Exception as e:
        print(f"\n[認証エラー] {e}\n", file=sys.stderr)
        if args.notify:
            send_notification("Googleフォト 認証エラー", str(e))
        sys.exit(1)

    # 2. 対象ファイルの収集
    files = collect_files(args.paths)
    if not files:
        print("アップロード対象の画像・動画が見つかりませんでした。")
        if args.notify:
            send_notification("Googleフォト", "対象のメディアファイルが見つかりませんでした。")
        return

    total_files = len(files)
    print(f"\n対象ファイル数: {total_files} 件")
    if args.notify:
        send_notification("Googleフォト アップロード開始", f"{total_files} 件のアップロードを開始しました...")

    uploader = GooglePhotosUploader(creds)

    # アルバム指定時の処理
    album_id = None
    if args.album:
        try:
            print(f"アルバム '{args.album}' を作成・準備中...")
            alb_res = uploader.create_album(args.album)
            album_id = alb_res.get("id")
            print(f"アルバム準備完了 (ID: {album_id})")
        except Exception as e:
            print(f"アルバム作成警告: {e}（メインライブラリにアップロードします）", file=sys.stderr)

    # 3. アップロード実行
    start_time = time.time()
    success_count = 0
    fail_count = 0
    failed_files = []

    # バッチ処理（最大50件ごと）
    BATCH_SIZE = 50
    
    # 段階1: uploadToken の取得
    with tqdm(total=total_files, desc="アップロード中", unit="file") as pbar:
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
                fail_count += 1
                failed_files.append((file_path.name, str(e)))
                print(f"\nアップロード失敗 ({file_path.name}): {e}", file=sys.stderr)
            
            # バッチサイズに達したか末尾なら batchCreate を実行
            if len(tokens_batch) >= BATCH_SIZE:
                success_count += _commit_batch(uploader, tokens_batch, album_id, failed_files)
                tokens_batch = []
            
            pbar.update(1)

        if tokens_batch:
            success_count += _commit_batch(uploader, tokens_batch, album_id, failed_files)

    elapsed = time.time() - start_time
    print("\n" + "=" * 40)
    print(f"完了! 成功: {success_count} 件 / 失敗: {len(failed_files)} 件 ({elapsed:.1f} 秒)")
    if failed_files:
        print("\n失敗したファイル:")
        for fname, err in failed_files:
            print(f"  - {fname}: {err}")
    print("=" * 40)

    if args.notify:
        if len(failed_files) == 0:
            send_notification(
                "Googleフォト アップロード完了",
                f"{success_count} 件のメディアを正常にアップロードしました。",
                subtitle=f"所要時間: {elapsed:.1f}秒"
            )
        else:
            send_notification(
                "Googleフォト アップロード完了 (一部失敗あり)",
                f"成功: {success_count} 件 / 失敗: {len(failed_files)} 件",
                subtitle=f"所要時間: {elapsed:.1f}秒"
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
            failed_files.append((it["file_name"], f"batchCreate失敗: {e}"))
        return 0

if __name__ == "__main__":
    main()

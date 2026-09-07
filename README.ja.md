# Google Photos Uploader for macOS

[English README](README.md) | **日本語**

macOSで画像や動画をオリジナル画質のままGoogleフォトへ簡単に直接アップロードできるツールです。
Finderでの右クリック（クイックアクション）、ドラッグ＆ドロップ、ターミナルCLIコマンドに対応しています。

---

## 3つの利用方法

### 1. Finderの右クリック（クイックアクション）
1. Finderで画像や動画（またはフォルダ）を選択
2. 右クリック（副ボタンクリック） > **[クイックアクション]** > **[Upload to Google Photos]** をクリック
3. アップロードが実行され、完了時にmacOS通知センターに結果が表示されます

### 2. ドラッグ＆ドロップ用アプリ
- `Upload to Google Photos.app` にファイルやフォルダをドラッグ＆ドロップするだけでアップロードできます。
- アプリをダブルクリックすると、ファイル選択ダイアログまたは認証・ステータス確認画面が開きます。
- 必要に応じてDockやデスクトップ、`/Applications`に配置して利用できます。

### 3. ターミナル CLI コマンド (`gphotos-upload`)
```bash
# 1枚または複数のファイルをアップロード
gphotos-upload photo1.jpg photo2.heic

# フォルダごと再帰的にアップロード
gphotos-upload ~/Pictures/Trip2026/

# アルバムを指定してアップロード（存在しない場合は自動作成）
gphotos-upload --album "My Vacation" photo.jpg

# 完了時にデスクトップ通知を表示
gphotos-upload --notify photo.jpg

# 現在の設定・認証状態を確認
gphotos-upload --status
```

---

## 対応ファイル形式（すべてオリジナル品質でアップロード）

- **画像**: JPEG (`.jpg`, `.jpeg`), PNG (`.png`), HEIC/HEIF (`.heic`, `.heif`), WebP (`.webp`), GIF (`.gif`), TIFF (`.tif`, `.tiff`), BMP (`.bmp`), RAW (`.dng`, `.cr2`, `.nef`, `.arw`, `.rw2`)
- **動画**: MP4 (`.mp4`), MOV (`.mov`), M4V (`.m4v`), AVI (`.avi`), MKV (`.mkv`), MPEG (`.mpg`, `.mpeg`)

---

## 初回セットアップ手順

本ツールはGoogle Photos Library APIを利用して安全に直接アップロードを行います。
利用開始前に、ユーザー自身のGoogleアカウントでOAuthクライアント（無料）を1度だけ作成する必要があります。

### 手順 1: Google Cloud Console での準備
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセスします。
2. 上部のプロジェクト選択メニューから **「新しいプロジェクト」** を作成します（プロジェクト名: `gphotos-uploader` など任意）。
3. ナビゲーションメニューから **「APIとサービス」 > 「ライブラリ」** を開き、**「Photos Library API」** を検索して **有効にする** をクリックします。
4. **「APIとサービス」 > 「OAuth 同意画面」** を開き、以下を設定します:
   - User Type: **「外部」** を選択して「作成」
   - アプリ情報（アプリ名: `gphotos-uploader`、ユーザーサポートメール・デベロッパー連絡先にご自身のGmailアドレスを入力）
   - 「保存して次へ」を進め、**「テストユーザー」** の画面で **ご自身のGoogleアカウント（Gmailアドレス）を追加** します。（※重要: テストユーザーに追加していないと認証時にエラーになります）
5. **「APIとサービス」 > 「認証情報」** を開き、**「認証情報を作成」 > 「OAuth クライアント ID」** を選択します:
   - アプリケーションの種類: **「デスクトップ アプリ」**
   - 名前: `gphotos-uploader-mac`（任意）
   - 「作成」をクリック
6. 作成されたクライアントの右側にあるダウンロードアイコンをクリックし、JSONファイルをダウンロードします。
7. ダウンロードしたファイルをリネームし、次のいずれかに配置します:
   - `credentials.json`（リポジトリルート）
   - または `~/.config/gphotos-uploader/credentials.json`

### 手順 2: インストールスクリプトの実行
```bash
./setup_macos.sh
```
Finderクイックアクションの登録、macOS Appのコンパイル、CLIのシンボリックリンク設定が全自動で行われます。

### 手順 3: 初回ログイン認証
ターミナルで以下のコマンドを実行します:
```bash
gphotos-upload --auth
```
- 自動的にブラウザが立ち上がり、Googleのログイン・アクセス許可画面が表示されます。
- 「このアプリはGoogleで確認されていません」と表示された場合は、**「詳細」 > 「（安全ではないページ）に移動」** をクリックして許可してください（自身が作成したアプリのため安全です）。
- 認証に成功するとトークンが `~/.config/gphotos-uploader/token.json` に安全に保存され、以後は再認証なしで自動更新されます。

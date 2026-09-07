#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== Google Photos Uploader セットアップ ==="
echo "ディレクトリ: $DIR"

# 1. venv作成とパッケージインストール
if [ ! -d "$DIR/venv" ]; then
    echo "[1/4] Python仮想環境を作成しています..."
    python3 -m venv "$DIR/venv"
fi

echo "[2/4] 依存ライブラリをインストールしています..."
"$DIR/venv/bin/pip" install --quiet --upgrade pip
"$DIR/venv/bin/pip" install --quiet -r "$DIR/requirements.txt"

# 2. CLIシンボリックリンク作成
echo "[3/4] CLIコマンド (gphotos-upload) を設定しています..."
mkdir -p "$HOME/.local/bin"
ln -sf "$DIR/bin/gphotos-upload" "$HOME/.local/bin/gphotos-upload"

# 3. macOS アプリケーション & クイックアクションの配置
echo "[4/4] macOS Finder クイックアクション & アプリを配置しています..."
mkdir -p "$HOME/Library/Services"
cp -R "$DIR/Googleフォトへアップロード.workflow" "$HOME/Library/Services/"

osacompile -o "$DIR/Googleフォトへアップロード.app" "$DIR/droplet.applescript"

echo ""
echo "=== セットアップ完了 ==="
"$DIR/bin/gphotos-upload" --status
echo ""
echo "次のステップ:"
echo "1. Google Cloud Console で作成した 'credentials.json' を $DIR/ または ~/.config/gphotos-uploader/ に配置してください。"
echo "2. 配置後、ターミナルで 'gphotos-upload --auth' を実行し、ブラウザで一度ログイン認証を行ってください。"
echo "3. 認証完了後は、Finderで画像を右クリック > [クイックアクション] > [Googleフォトへアップロード] で即座にアップロードできます。"

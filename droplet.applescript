on open droppedItems
    set posixPaths to ""
    repeat with anItem in droppedItems
        set posixPaths to posixPaths & " " & quoted form of POSIX path of anItem
    end repeat
    do shell script "/Users/nen/dev/_stable/gphotos-uploader/venv/bin/python /Users/nen/dev/_stable/gphotos-uploader/cli.py --notify" & posixPaths
end open

on run
    set choice to button returned of (display dialog "Googleフォト 簡単アップローダー\n\nファイルを選択してアップロードするか、ステータス/認証を実行します。" buttons {"キャンセル", "ステータス/認証", "ファイル選択"} default button "ファイル選択")
    if choice is "ファイル選択" then
        set selectedFiles to choose file with prompt "Googleフォトにアップロードする画像・動画を選択してください:" with multiple selections allowed
        set posixPaths to ""
        repeat with anItem in selectedFiles
            set posixPaths to posixPaths & " " & quoted form of POSIX path of anItem
        end repeat
        do shell script "/Users/nen/dev/_stable/gphotos-uploader/venv/bin/python /Users/nen/dev/_stable/gphotos-uploader/cli.py --notify" & posixPaths
    else if choice is "ステータス/認証" then
        tell application "Terminal"
            activate
            do script "cd /Users/nen/dev/_stable/gphotos-uploader && ./venv/bin/python cli.py --status && ./venv/bin/python cli.py --auth"
        end tell
    end if
end run

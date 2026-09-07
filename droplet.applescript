on open droppedItems
    set posixPaths to ""
    repeat with anItem in droppedItems
        set posixPaths to posixPaths & " " & quoted form of POSIX path of anItem
    end repeat
    do shell script "/Users/nen/dev/_stable/gphotos-uploader/venv/bin/python /Users/nen/dev/_stable/gphotos-uploader/cli.py --notify" & posixPaths
end open

on run
    set choice to button returned of (display dialog "Google Photos Uploader\n\nSelect photos/videos to upload, or check authentication status." buttons {"Cancel", "Status / Auth", "Choose Files"} default button "Choose Files")
    if choice is "Choose Files" then
        set selectedFiles to choose file with prompt "Select photos or videos to upload to Google Photos:" with multiple selections allowed
        set posixPaths to ""
        repeat with anItem in selectedFiles
            set posixPaths to posixPaths & " " & quoted form of POSIX path of anItem
        end repeat
        do shell script "/Users/nen/dev/_stable/gphotos-uploader/venv/bin/python /Users/nen/dev/_stable/gphotos-uploader/cli.py --notify" & posixPaths
    else if choice is "Status / Auth" then
        tell application "Terminal"
            activate
            do script "cd /Users/nen/dev/_stable/gphotos-uploader && ./venv/bin/python cli.py --status && ./venv/bin/python cli.py --auth"
        end tell
    end if
end run

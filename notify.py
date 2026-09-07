import subprocess
import shlex

def send_notification(title: str, message: str, subtitle: str = "", sound: str = "default"):
    """macOSのデスクトップ通知を表示します"""
    script = f'display notification "{shlex.quote(message).strip("\'")}" with title "{shlex.quote(title).strip("\'")}"'
    if subtitle:
        script += f' subtitle "{shlex.quote(subtitle).strip("\'")}"'
    if sound:
        script += f' sound name "{sound}"'
    
    try:
        subprocess.run(["osascript", "-e", script], check=False)
    except Exception:
        pass

if __name__ == "__main__":
    send_notification("Googleフォト", "テスト通知です")

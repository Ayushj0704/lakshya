"""
remind_notify.py -- Notification script called by Windows Task Scheduler.
Usage: python remind_notify.py <message text>
"""

import sys
import subprocess


def show_notification(message):
    # --- Primary: win10toast ---
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast("Lakshya Reminder", message, duration=10, threaded=False)
        return
    except ImportError:
        pass
    except Exception:
        pass

    # --- Fallback: new console window ---
    try:
        safe_msg = (
            message.replace("&", "^&").replace("|", "^|")
            .replace("<", "^<").replace(">", "^>")
        )
        subprocess.Popen(
            ["cmd", "/c", "echo Lakshya Reminder: {} && pause".format(safe_msg)],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        return
    except Exception:
        pass

    # --- Last resort: PowerShell MessageBox ---
    try:
        ps_script = (
            "Add-Type -AssemblyName PresentationFramework;"
            "[System.Windows.MessageBox]::Show('{}', 'Lakshya Reminder')".format(
                message.replace("'", "`'")
            )
        )
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except Exception:
        pass


if __name__ == "__main__":
    msg = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "Time to check your Lakshya goals!"
    )
    show_notification(msg)

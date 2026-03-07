"""
WhatsApp messaging utility using pywhatkit.
Opens WhatsApp Web and sends messages automatically.
"""
import threading
import time
from typing import Optional


def _send_whatsapp_background(phone: str, message: str, tab_close: bool = True,
                               close_time: int = 5, wait_time: int = 20):
    try:
        import pywhatkit as kit
        # Remove non-digit characters except leading +
        cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
        if not cleaned.startswith("+"):
            cleaned = "+91" + cleaned  # default country code India
        kit.sendwhatmsg_instantly(
            cleaned, message,
            wait_time=wait_time,
            tab_close=tab_close,
            close_time=close_time
        )
    except Exception as e:
        print(f"[WhatsApp Error] {e}")


def send_message(phone: str, message: str, async_send: bool = True) -> bool:
    """
    Send a WhatsApp message.
    async_send=True sends in background thread so UI doesn't block.
    Returns True if dispatch was initiated (not guaranteed delivery).
    """
    if not phone or not message:
        return False
    if async_send:
        t = threading.Thread(
            target=_send_whatsapp_background,
            args=(phone, message),
            daemon=True
        )
        t.start()
        return True
    else:
        try:
            _send_whatsapp_background(phone, message)
            return True
        except Exception:
            return False


def format_reminder_message(template: str, name: str) -> str:
    return template.replace("{name}", name)


def format_removal_message(template: str, name: str) -> str:
    return template.replace("{name}", name)

"""
Utility functions for Admin 2FA via Telegram Bot.
"""
import logging
import secrets
import time
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_otp(length: int = 6) -> str:
    """
    Returns a cryptographically secure numeric OTP string of the given length.
    Uses secrets.choice to guarantee uniform randomness across all digits.
    """
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


def send_telegram_otp(chat_id: str, otp: str) -> tuple[bool, str]:
    """
    Sends a formatted 6-digit OTP message to a Telegram chat via the Bot API.

    Args:
        chat_id: Numeric Telegram Chat ID of the recipient admin.
        otp:     The 6-digit OTP string to send.

    Returns:
        (True, message_id_str) on success.
        (False, error_description) on failure.
    """
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '').strip()
    if not token:
        msg = "TELEGRAM_BOT_TOKEN is not configured in settings/environment."
        logger.error(msg)
        return False, msg

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    text = (
        "🏫 *Mid Point School — Admin 2FA*\n\n"
        "Your one-time login verification code is:\n\n"
        f"🔐 *`{otp}`*\n\n"
        "_This code is valid for *5 minutes*. Do not share it with anyone._"
    )

    try:
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
        data = response.json()

        if response.ok and data.get("ok"):
            msg_id = str(data["result"]["message_id"])
            logger.info(f"Telegram OTP sent to chat_id={chat_id}. Message ID: {msg_id}")
            return True, msg_id

        # Telegram returned an error payload
        err = data.get("description", "Unknown Telegram API error.")
        logger.error(f"Telegram API error for chat_id={chat_id}: {err}")
        return False, err

    except requests.exceptions.Timeout:
        err = "Telegram API request timed out. Check your internet connection."
        logger.error(err)
        return False, err

    except requests.exceptions.ConnectionError:
        err = "Could not reach Telegram servers. Check your internet connection."
        logger.error(err)
        return False, err

    except Exception as exc:
        err = f"Unexpected error sending Telegram OTP: {exc}"
        logger.error(err)
        return False, err


def can_resend_otp(request, cooldown_seconds: int = 60) -> tuple[bool, int]:
    """
    Rate-limits OTP resend requests.
    Returns (can_resend, seconds_remaining).
    """
    last_sent_at = request.session.get('otp_last_sent_at')
    if not last_sent_at:
        return True, 0
    elapsed = int(time.time()) - int(last_sent_at)
    if elapsed >= cooldown_seconds:
        return True, 0
    return False, cooldown_seconds - elapsed

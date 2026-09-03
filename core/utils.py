"""
Utility functions for Admin 2FA and Broadcast Notifications via Telegram Bot.
"""
import logging
import secrets
import time
from datetime import datetime
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def escape_markdown(text: str) -> str:
    """
    Escapes Telegram Markdown (V1) special characters in dynamic user strings:
    _ (underscore), * (asterisk), ` (backtick), [ (bracket)
    """
    if not text:
        return ""
    escape_chars = ['_', '*', '`', '[']
    escaped_text = str(text)
    for char in escape_chars:
        escaped_text = escaped_text.replace(char, f"\\{char}")
    return escaped_text


def send_telegram_message(chat_id: str, message_text: str, parse_mode: str = 'Markdown') -> tuple[bool, str]:
    """
    Core function using the requests library to dispatch messages via the Telegram Bot API.
    Includes comprehensive error handling and automatic plain-text fallback if Markdown
    parsing fails on Telegram's end.

    Args:
        chat_id: Numeric or string Telegram Chat ID of recipient.
        message_text: The formatted text message to send.
        parse_mode: 'Markdown', 'HTML', or None.

    Returns:
        (True, message_id_or_status) on success.
        (False, error_description) on failure.
    """
    if not chat_id:
        return False, "Chat ID is required but was empty or None."

    token = (getattr(settings, 'TELEGRAM_BOT_TOKEN', '') or '8922551001:AAFgIZkymE0UGzmm0wOjhYfPZEcMB8m43oA').strip()
    if not token:
        msg = "TELEGRAM_BOT_TOKEN is not configured in settings/environment."
        logger.error(msg)
        return False, msg

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": str(chat_id).strip(),
        "text": message_text,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()

        if response.ok and data.get("ok"):
            msg_id = str(data["result"]["message_id"])
            logger.info(f"Telegram message delivered to chat_id={chat_id}. Message ID: {msg_id}")
            return True, msg_id

        # If Telegram rejected due to markdown formatting entities, retry in plain text
        err = data.get("description", "Unknown Telegram API error.")
        if parse_mode and ("can't parse entities" in err.lower() or "parsing" in err.lower()):
            logger.warning(f"Telegram Markdown parse failed ({err}). Retrying without parse_mode...")
            fallback_payload = {"chat_id": str(chat_id).strip(), "text": message_text}
            fallback_res = requests.post(url, json=fallback_payload, timeout=10)
            fallback_data = fallback_res.json()
            if fallback_res.ok and fallback_data.get("ok"):
                msg_id = str(fallback_data["result"]["message_id"])
                logger.info(f"Telegram message sent via plain-text fallback to chat_id={chat_id}.")
                return True, msg_id
            err = fallback_data.get("description", err)

        logger.error(f"Telegram API error for chat_id={chat_id}: {err}")
        return False, err

    except requests.exceptions.Timeout:
        err = "Telegram API request timed out."
        logger.error(err)
        return False, err

    except requests.exceptions.ConnectionError:
        err = "Could not connect to Telegram servers. Check network connection."
        logger.error(err)
        return False, err

    except Exception as exc:
        err = f"Unexpected error sending Telegram message: {exc}"
        logger.error(err)
        return False, err


def generate_otp(length: int = 6) -> str:
    """
    Returns a cryptographically secure numeric OTP string of the given length.
    Uses secrets.choice to guarantee uniform randomness across all digits.
    """
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


def send_telegram_otp(chat_id: str, otp: str) -> tuple[bool, str]:
    """
    Formats and dispatches a 6-digit OTP message to a specific admin via Telegram.

    Args:
        chat_id: Numeric Telegram Chat ID of the recipient admin.
        otp: The 6-digit OTP string to send.

    Returns:
        (True, message_id_str) on success.
        (False, error_description) on failure.
    """
    text = (
        "🏫 *Mid Point School — Admin 2FA*\n\n"
        "Your one-time login verification code is:\n\n"
        f"🔐 *`{otp}`*\n\n"
        "_This code is valid for *5 minutes*. Do not share it with anyone._"
    )
    return send_telegram_message(chat_id, text, parse_mode="Markdown")


def send_inquiry_telegram_alert(inquiry_data) -> dict:
    """
    Fetches all registered admins' chat IDs and broadcasts new website inquiry details:
    (Name, Phone, Email, Class/Course, Message).

    Args:
        inquiry_data: Can be an Inquiry model instance or a dict with:
                      {'name', 'phone'/'mobile', 'email', 'subject'/'course', 'message'}

    Returns:
        dict: {'total': int, 'sent': int, 'failed': int, 'recipients': list}
    """
    from core.models import AdminProfile

    # Normalize data whether input is a model instance or a dictionary
    if hasattr(inquiry_data, 'name'):
        name = getattr(inquiry_data, 'name', '')
        phone = getattr(inquiry_data, 'mobile', '') or getattr(inquiry_data, 'phone', '')
        email = getattr(inquiry_data, 'email', '') or 'Not provided'
        subject_course = getattr(inquiry_data, 'subject', '') or getattr(inquiry_data, 'course', 'General Inquiry')
        message = getattr(inquiry_data, 'message', '')
        timestamp = getattr(inquiry_data, 'created_at', None)
    else:
        name = inquiry_data.get('name', '')
        phone = inquiry_data.get('mobile') or inquiry_data.get('phone', '')
        email = inquiry_data.get('email') or 'Not provided'
        subject_course = inquiry_data.get('subject') or inquiry_data.get('course') or inquiry_data.get('class_name', 'General Inquiry')
        message = inquiry_data.get('message', '')
        timestamp = inquiry_data.get('created_at')

    time_str = timestamp.strftime('%d %b %Y, %I:%M %p') if isinstance(timestamp, datetime) else datetime.now().strftime('%d %b %Y, %I:%M %p')

    # Format the broadcast message with clean Markdown
    alert_text = (
        "📬 *NEW WEBSITE INQUIRY RECEIVED*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Name:* {escape_markdown(name)}\n"
        f"📞 *Phone:* {escape_markdown(phone)}\n"
        f"📧 *Email:* {escape_markdown(email)}\n"
        f"📚 *Class / Course:* {escape_markdown(subject_course)}\n"
        "💬 *Message:*\n"
        f"{escape_markdown(message)}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏰ *Received at:* `{time_str}`"
    )

    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '').strip()
    bot_id = token.split(':')[0] if ':' in token else ''

    admin_profiles = AdminProfile.objects.exclude(
        telegram_chat_id__isnull=True
    ).exclude(
        telegram_chat_id__exact=''
    )

    # Deduplicate chat IDs so each admin receives exactly ONE message
    unique_chat_ids = set()
    for profile in admin_profiles:
        cid = (profile.telegram_chat_id or '').strip()
        if cid and cid != bot_id:
            unique_chat_ids.add(cid)

    results = {
        "total": len(unique_chat_ids),
        "sent": 0,
        "failed": 0,
        "recipients": []
    }

    for chat_id in sorted(unique_chat_ids):
        success, info = send_telegram_message(chat_id, alert_text, parse_mode="Markdown")
        results["recipients"].append({"chat_id": chat_id, "success": success, "info": info})
        if success:
            results["sent"] += 1
        else:
            results["failed"] += 1
            logger.warning(f"Failed to send website inquiry alert to admin chat_id={chat_id}: {info}")

    logger.info(f"Broadcasted inquiry alert to {results['sent']}/{results['total']} unique admin chat IDs.")
    return results


def send_complaint_telegram_alert(complaint_data) -> dict:
    """
    Fetches all registered admins' chat IDs and broadcasts student complaint details:
    (Student Name, Roll No, Class/Sec, Subject, Category, Description).

    Args:
        complaint_data: Can be a Complaint model instance or a dict with:
                        {'student_name', 'roll_no', 'class_sec', 'subject', 'category', 'description'}

    Returns:
        dict: {'total': int, 'sent': int, 'failed': int, 'recipients': list}
    """
    from core.models import AdminProfile

    # Normalize data whether input is a model instance or a dictionary
    if hasattr(complaint_data, 'student'):
        student = complaint_data.student
        student_name = student.name if student else "Unknown Student"
        roll_no = getattr(student, 'roll_number', None) or getattr(student, 'id', 'N/A')
        class_sec = str(student.student_class) if student and student.student_class else "N/A"
        subject = getattr(complaint_data, 'subject', '')
        category = getattr(complaint_data, 'category', None) or "Student Grievance"
        description = getattr(complaint_data, 'description', '')
        timestamp = getattr(complaint_data, 'created_at', None)
    else:
        student_name = complaint_data.get('student_name', 'Student')
        roll_no = complaint_data.get('roll_no', 'N/A')
        class_sec = complaint_data.get('class_sec', 'N/A')
        subject = complaint_data.get('subject', 'Grievance')
        category = complaint_data.get('category', 'Student Grievance')
        description = complaint_data.get('description', '')
        timestamp = complaint_data.get('created_at')

    time_str = timestamp.strftime('%d %b %Y, %I:%M %p') if isinstance(timestamp, datetime) else datetime.now().strftime('%d %b %Y, %I:%M %p')

    # Format the broadcast message with clean Markdown
    alert_text = (
        "🚨 *NEW STUDENT COMPLAINT FILED*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎓 *Student:* {escape_markdown(student_name)} (ID: #{roll_no})\n"
        f"🏫 *Class & Section:* {escape_markdown(class_sec)}\n"
        f"🏷️ *Category:* {escape_markdown(category)}\n"
        f"📌 *Subject:* {escape_markdown(subject)}\n"
        "📝 *Complaint Details:*\n"
        f"{escape_markdown(description)}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏰ *Submitted at:* `{time_str}`"
    )

    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '').strip()
    bot_id = token.split(':')[0] if ':' in token else ''

    admin_profiles = AdminProfile.objects.exclude(
        telegram_chat_id__isnull=True
    ).exclude(
        telegram_chat_id__exact=''
    )

    # Deduplicate chat IDs so each admin receives exactly ONE message
    unique_chat_ids = set()
    for profile in admin_profiles:
        cid = (profile.telegram_chat_id or '').strip()
        if cid and cid != bot_id:
            unique_chat_ids.add(cid)

    results = {
        "total": len(unique_chat_ids),
        "sent": 0,
        "failed": 0,
        "recipients": []
    }

    for chat_id in sorted(unique_chat_ids):
        success, info = send_telegram_message(chat_id, alert_text, parse_mode="Markdown")
        results["recipients"].append({"chat_id": chat_id, "success": success, "info": info})
        if success:
            results["sent"] += 1
        else:
            results["failed"] += 1
            logger.warning(f"Failed to send student complaint alert to admin chat_id={chat_id}: {info}")

    logger.info(f"Broadcasted complaint alert to {results['sent']}/{results['total']} unique admin chat IDs.")
    return results


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

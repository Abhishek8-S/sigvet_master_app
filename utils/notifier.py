"""
utils/notifier.py — WhatsApp Notification Helper (Twilio)
===========================================================
Provides a single public function:

    send_whatsapp_via_twilio(to_number, message, config) -> (bool, str)

Usage:
    from utils.notifier import send_whatsapp_via_twilio
    ok, detail = send_whatsapp_via_twilio("+919876543210", "Hello!", config)
"""

from typing import Tuple


def send_whatsapp_via_twilio(
    to_number: str,
    message: str,
    config: dict,
) -> Tuple[bool, str]:
    """
    Send a WhatsApp message via Twilio.

    Parameters
    ----------
    to_number : str
        Recipient phone number, with country code (e.g. ``+919876543210``).
        The ``whatsapp:`` prefix is added automatically if absent.
    message : str
        Plain-text (or template) message body.
    config : dict
        The application config dict (from ``get_config()``).
        Expected keys under ``app``:
            - ``twilio_account_sid``
            - ``twilio_auth_token``
            - ``twilio_from_number``  (e.g. ``whatsapp:+14155238886``)

    Returns
    -------
    (success, detail) : (bool, str)
        ``success`` is ``True`` when Twilio accepted the message (SID returned).
        ``detail`` contains the message SID on success, or an error string on failure.
    """
    try:
        from twilio.rest import Client
    except ImportError:
        return False, "Twilio SDK not installed. Run: pip install twilio"

    app_cfg = config.get("app", {})
    account_sid = app_cfg.get("twilio_account_sid", "")
    auth_token  = app_cfg.get("twilio_auth_token", "")
    from_number = app_cfg.get("twilio_from_number", "")

    # Validate credentials are not still set to placeholder values
    placeholder_sid   = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    placeholder_token = "your_auth_token_here"

    if account_sid == placeholder_sid or auth_token == placeholder_token:
        return False, (
            "Twilio credentials are not configured. "
            "Update 'twilio_account_sid' and 'twilio_auth_token' in config.yaml."
        )
    if not account_sid or not auth_token or not from_number:
        return False, (
            "Incomplete Twilio config. Ensure 'twilio_account_sid', "
            "'twilio_auth_token', and 'twilio_from_number' are set in config.yaml."
        )

    # Normalise numbers to include whatsapp: prefix
    wa_to   = to_number   if to_number.startswith("whatsapp:")   else f"whatsapp:{to_number}"
    wa_from = from_number if from_number.startswith("whatsapp:") else f"whatsapp:{from_number}"

    try:
        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            body=message,
            from_=wa_from,
            to=wa_to,
        )
        return True, f"Sent (SID: {msg.sid})"
    except Exception as exc:
        return False, str(exc)

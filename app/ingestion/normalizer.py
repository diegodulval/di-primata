from app.ingestion.models import IncomingMessage


def normalize(payload: dict) -> IncomingMessage:
    """Converte o form-payload do Twilio para IncomingMessage canônico."""
    raw_from = payload.get("From", "")
    phone = raw_from.removeprefix("whatsapp:")

    num_media = int(payload.get("NumMedia", 0))
    media_urls = [
        payload[f"MediaUrl{i}"]
        for i in range(num_media)
        if f"MediaUrl{i}" in payload
    ]

    return IncomingMessage(
        phone=phone,
        profile_name=payload.get("ProfileName", ""),
        body=payload.get("Body", ""),
        message_sid=payload.get("MessageSid", ""),
        num_media=num_media,
        media_urls=media_urls,
    )

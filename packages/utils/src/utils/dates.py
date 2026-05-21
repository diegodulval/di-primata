from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None

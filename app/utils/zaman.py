from datetime import datetime, timezone
from zoneinfo import ZoneInfo


TURKIYE_SAAT_DILIMI = ZoneInfo("Europe/Istanbul")


def turkiye_saati(zaman: datetime | None) -> datetime | None:
    """Veritabanındaki UTC zamanı Türkiye yerel saatine dönüştürür."""
    if zaman is None:
        return None
    utc_zamani = zaman.replace(tzinfo=timezone.utc) if zaman.tzinfo is None else zaman.astimezone(timezone.utc)
    return utc_zamani.astimezone(TURKIYE_SAAT_DILIMI)


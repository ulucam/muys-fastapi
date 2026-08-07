"""Güvenlik bağımlılıkları.

Ortak yetki denetimleri artık ``app.dependencies`` içinde tanımlıdır;
bu modül mevcut importları kırmamak için onları yeniden dışa aktarır.
"""

from app.dependencies import kullanici_yonetim_kontrol, yetki_kontrol  # noqa: F401

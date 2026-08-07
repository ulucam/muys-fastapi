"""Web Push için bir kez kullanılacak VAPID anahtar çifti üretir."""

import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def base64url(veri: bytes) -> str:
    return base64.urlsafe_b64encode(veri).rstrip(b"=").decode("ascii")


def anahtar_uret() -> tuple[str, str]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_der = private_key.private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_point = private_key.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    return base64url(public_point), base64url(private_der)


if __name__ == "__main__":
    public_key, private_key = anahtar_uret()
    print("Bu değerleri Render ortam değişkenlerine veya yerel .env dosyasına ekleyin:")
    print(f"VAPID_PUBLIC_KEY={public_key}")
    print(f"VAPID_PRIVATE_KEY={private_key}")
    print("VAPID_SUBJECT=mailto:bildirim@firma.com")

import io
import base64
from PIL import Image


def compress_image(
    data: bytes, max_dimension: int = 1280, quality: int = 70
) -> tuple[bytes, int, int]:
    """Resize and compress image, return (jpeg_bytes, width, height)."""
    img = Image.open(io.BytesIO(data))
    w, h = img.size
    if max(w, h) > max_dimension:
        ratio = max_dimension / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        w, h = img.size
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality)
    return buf.getvalue(), w, h


def to_b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def screenshot_to_b64(data: bytes, max_dimension: int = 1280, quality: int = 70) -> str:
    compressed, _, _ = compress_image(data, max_dimension, quality)
    return to_b64(compressed)

from __future__ import annotations

from io import BytesIO
from pathlib import PurePosixPath

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def _open_image(file) -> Image.Image:
    img = Image.open(file)
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def _variant_name(original_name: str, suffix: str) -> str:
    p = PurePosixPath(original_name or "image")
    return str(p.with_name(f"{p.stem}__{suffix}.webp"))


def compress_webp(
    file,
    *,
    original_name: str,
    max_size=(1600, 1600),
    quality: int = 82,
    suffix: str = "main",
) -> ContentFile:
    img = _open_image(file)
    img.thumbnail(max_size)

    buf = BytesIO()
    img.save(buf, format="WEBP", quality=quality, method=6)
    buf.seek(0)

    return ContentFile(buf.read(), name=_variant_name(original_name, suffix))


def thumb_webp(
    file,
    *,
    original_name: str,
    width: int,
    quality: int = 80,
) -> ContentFile:
    img = _open_image(file)
    w, h = img.size

    if w > width:
        new_h = int(h * (width / w))
        img = img.resize((width, new_h), Image.Resampling.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="WEBP", quality=quality, method=6)
    buf.seek(0)

    return ContentFile(buf.read(), name=_variant_name(original_name, f"{width}w"))

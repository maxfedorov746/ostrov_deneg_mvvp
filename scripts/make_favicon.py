"""Build the small ICO fallback from the same island-and-flag motif as favicon.svg."""

import struct
import zlib
from pathlib import Path


SIZE = 32
ROOT = Path(__file__).resolve().parents[1]


def pixel(x: int, y: int) -> tuple[int, int, int, int]:
    if (x < 5 and y < 5 and (x - 5) ** 2 + (y - 5) ** 2 > 25) or (
        x > 26 and y < 5 and (x - 26) ** 2 + (y - 5) ** 2 > 25
    ) or (x < 5 and y > 26 and (x - 5) ** 2 + (y - 26) ** 2 > 25) or (
        x > 26 and y > 26 and (x - 26) ** 2 + (y - 26) ** 2 > 25
    ):
        return (0, 0, 0, 0)
    color = (23, 63, 72, 255)
    if ((x - 16) / 13) ** 2 + ((y - 23) / 7) ** 2 <= 1:
        color = (233, 220, 186, 255)
    if ((x - 16) / 10) ** 2 + ((y - 23) / 4) ** 2 <= 1:
        color = (117, 164, 134, 255)
    if x == 15 and 8 <= y <= 22:
        color = (16, 47, 54, 255)
    if 16 <= x <= 25 and 9 <= y <= 16 and y <= 9 + (x - 16) / 2 + 2:
        color = (218, 120, 88, 255)
    return color


def chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(
        ">I", zlib.crc32(kind + data) & 0xFFFFFFFF
    )


rows = b"".join(b"\0" + bytes(channel for x in range(SIZE) for channel in pixel(x, y))
                for y in range(SIZE))
png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))
ico = (struct.pack("<HHH", 0, 1, 1)
       + struct.pack("<BBBBHHII", SIZE, SIZE, 0, 0, 1, 32, len(png), 22) + png)
(ROOT / "frontend" / "public" / "favicon.ico").write_bytes(ico)

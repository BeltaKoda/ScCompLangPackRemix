"""
Minimal P4K file reader for Star Citizen's Data.p4k.

P4K files are ZIP64 archives with a non-standard preamble in the central
directory. This module handles that quirk and supports zstandard-compressed
entries (compress_type=100).

Dependencies: zstandard, pycryptodome (only if reading encrypted entries)
"""

import struct
import zipfile
from pathlib import Path

# P4K uses zstandard compression identified by type 100
ZIP_ZSTD = 100


class P4KEntry:
    """Represents a single file entry in a P4K archive."""
    __slots__ = ("filename", "compress_type", "compressed_size", "file_size",
                 "header_offset", "is_encrypted", "extra")

    def __init__(self):
        self.filename = ""
        self.compress_type = 0
        self.compressed_size = 0
        self.file_size = 0
        self.header_offset = 0
        self.is_encrypted = False
        self.extra = b""


class P4KFile:
    """Read-only access to Star Citizen P4K archives.

    Usage:
        p4k = P4KFile("/path/to/Data.p4k")
        data = p4k.read("Data/Localization/english/global.ini")
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.entries: list[P4KEntry] = []
        self._name_map: dict[str, P4KEntry] = {}
        self._parse_central_directory()

    def _parse_central_directory(self):
        """Parse the ZIP64 central directory, handling P4K's non-standard preamble."""
        with open(self.path, "rb") as fp:
            endrec = zipfile._EndRecData(fp)
            if not endrec:
                raise ValueError(f"Not a valid P4K/ZIP file: {self.path}")

            size_cd = endrec[zipfile._ECD_SIZE]
            offset_cd = endrec[zipfile._ECD_OFFSET]

            # Calculate concat offset (accounts for prepended data)
            concat = endrec[zipfile._ECD_LOCATION] - size_cd - offset_cd
            if endrec[zipfile._ECD_SIGNATURE] == zipfile.stringEndArchive64:
                concat -= zipfile.sizeEndCentDir64 + zipfile.sizeEndCentDir64Locator

            fp.seek(offset_cd + concat)
            cd_data = fp.read(size_cd)

        # P4K files may have a non-standard preamble before the first PK\x01\x02
        pk_sig = b"PK\x01\x02"
        first_pk = cd_data.find(pk_sig)
        if first_pk < 0:
            raise ValueError("No central directory entries found in P4K file")

        pos = first_pk
        while pos + zipfile.sizeCentralDir <= len(cd_data):
            if cd_data[pos:pos + 4] != pk_sig:
                break

            centdir = struct.unpack(
                zipfile.structCentralDir,
                cd_data[pos:pos + zipfile.sizeCentralDir],
            )

            fn_len = centdir[zipfile._CD_FILENAME_LENGTH]
            extra_len = centdir[zipfile._CD_EXTRA_FIELD_LENGTH]
            comment_len = centdir[zipfile._CD_COMMENT_LENGTH]
            entry_size = zipfile.sizeCentralDir + fn_len + extra_len + comment_len

            fn_raw = cd_data[pos + zipfile.sizeCentralDir:pos + zipfile.sizeCentralDir + fn_len]
            flags = centdir[zipfile._CD_FLAG_BITS]
            filename = fn_raw.decode("utf-8" if flags & 0x800 else "cp437")

            extra = cd_data[
                pos + zipfile.sizeCentralDir + fn_len:
                pos + zipfile.sizeCentralDir + fn_len + extra_len
            ]

            entry = P4KEntry()
            entry.filename = filename
            entry.compress_type = centdir[zipfile._CD_COMPRESS_TYPE]
            entry.compressed_size = centdir[zipfile._CD_COMPRESSED_SIZE]
            entry.file_size = centdir[zipfile._CD_UNCOMPRESSED_SIZE]
            entry.header_offset = centdir[zipfile._CD_LOCAL_HEADER_OFFSET]
            entry.extra = extra
            entry.is_encrypted = len(extra) >= 168 and extra[168] > 0x00

            # Resolve ZIP64 extended sizes
            _resolve_zip64(entry)

            self.entries.append(entry)
            # Normalize path separators for lookup
            self._name_map[filename.replace("\\", "/").lower()] = entry

            pos += entry_size

    def find(self, pattern: str) -> P4KEntry | None:
        """Find an entry by case-insensitive path (forward slashes)."""
        key = pattern.replace("\\", "/").lower()
        return self._name_map.get(key)

    def read(self, entry_or_path) -> bytes:
        """Read and decompress a file from the P4K archive."""
        if isinstance(entry_or_path, str):
            entry = self.find(entry_or_path)
            if entry is None:
                raise FileNotFoundError(f"Not found in P4K: {entry_or_path}")
        else:
            entry = entry_or_path

        with open(self.path, "rb") as fp:
            fp.seek(entry.header_offset)
            local_header = fp.read(30)
            lh = struct.unpack("<4sHHHHHIIIHH", local_header)
            local_fn_len = lh[-2]
            local_extra_len = lh[-1]

            fp.seek(entry.header_offset + 30 + local_fn_len + local_extra_len)
            compressed = fp.read(entry.compressed_size)

        if entry.is_encrypted:
            compressed = _decrypt(compressed)

        if entry.compress_type == ZIP_ZSTD:
            import zstandard as zstd
            dctx = zstd.ZstdDecompressor()
            return dctx.decompress(compressed, max_output_size=entry.file_size + 4096)
        elif entry.compress_type == zipfile.ZIP_STORED:
            return compressed
        elif entry.compress_type == zipfile.ZIP_DEFLATED:
            import zlib
            return zlib.decompress(compressed, -15)
        else:
            raise ValueError(f"Unsupported compression type: {entry.compress_type}")


def _resolve_zip64(entry: P4KEntry):
    """Parse ZIP64 extended information from the extra field."""
    extra = entry.extra
    offset = 0
    while offset + 4 < len(extra):
        tag, size = struct.unpack("<HH", extra[offset:offset + 4])
        if tag == 0x0001:  # ZIP64
            vals = [
                struct.unpack("<Q", extra[offset + 4 + i * 8:offset + 4 + (i + 1) * 8])[0]
                for i in range(size // 8)
            ]
            idx = 0
            if entry.file_size in (0xFFFFFFFF, 0xFFFFFFFFFFFFFFFF):
                entry.file_size = vals[idx]; idx += 1
            if entry.compressed_size == 0xFFFFFFFF:
                entry.compressed_size = vals[idx]; idx += 1
            if entry.header_offset == 0xFFFFFFFF:
                entry.header_offset = vals[idx]; idx += 1
            return
        offset += 4 + size


def _decrypt(data: bytes) -> bytes:
    """Decrypt AES-encrypted P4K entry data."""
    from Crypto.Cipher import AES
    key = b"\x5e\x7a\x20\x02\x30\x2e\xeb\x1a\x3b\xb6\x17\xc3\x0f\xde\x1e\x47"
    cipher = AES.new(key, AES.MODE_CBC, b"\x00" * 16)
    return cipher.decrypt(data)

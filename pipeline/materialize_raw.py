from __future__ import annotations

import argparse
import base64
import binascii
import ctypes
import os
import sys
from pathlib import Path

from pipeline.io import sha256_bytes


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = (ROOT / "data" / "raw").resolve()


def _read_stdin_line() -> bytes:
    if os.name != "nt" or not sys.stdin.isatty():
        return sys.stdin.buffer.readline()
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
    mode = ctypes.c_uint()
    if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        return sys.stdin.buffer.readline()
    echo_input = 0x0004
    kernel32.SetConsoleMode(handle, mode.value & ~echo_input)
    try:
        return sys.stdin.buffer.readline()
    finally:
        kernel32.SetConsoleMode(handle, mode.value)


def materialize_base64(
    encoded: bytes,
    output_path: Path,
    *,
    expected_sha256: str,
    expected_size: int,
    allowed_root: Path = RAW_ROOT,
) -> Path:
    """Decode connector bytes into ignored raw storage and verify the revision."""

    root = allowed_root.resolve()
    output = output_path.resolve()
    if output != root and root not in output.parents:
        raise ValueError(f"Raw output must remain under {root}")
    compact = b"".join(encoded.split())
    try:
        raw = base64.b64decode(compact, validate=True)
    except binascii.Error as error:
        raise ValueError("Connector payload is not valid base64") from error
    if len(raw) != expected_size:
        raise ValueError(
            f"Connector payload size mismatch: expected {expected_size}, got {len(raw)}"
        )
    actual_sha256 = sha256_bytes(raw)
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"Connector payload hash mismatch: expected {expected_sha256}, got {actual_sha256}"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
    temporary.write_bytes(raw)
    os.replace(temporary, output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize a base64 connector file into ignored raw storage"
    )
    parser.add_argument("output", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--size", type=int, required=True)
    args = parser.parse_args()
    path = materialize_base64(
        _read_stdin_line(),
        args.output,
        expected_sha256=args.sha256,
        expected_size=args.size,
    )
    print(path)


if __name__ == "__main__":
    main()

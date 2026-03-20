import re
from typing import Union

import base58
from Crypto.Hash import keccak as _crypto_keccak


class BadAddress(ValueError):
    pass

HEX_ADDRESS_REGEXP = re.compile("^(0x)?[0-9a-fA-F]{40}$")
TON_ADDRESS_REGEXP = re.compile("^(?:EQ|UQ|kQ|0Q)[0-9a-zA-Z_-]{46,48}$")
TON_RAW_ADDRESS_REGEXP = re.compile(r'^-?\d+:[0-9a-fA-F]{64}$')

def is_base58check_address(value: str) -> bool:
    return value[0] == "T" and len(base58.b58decode_check(value)) == 21


def is_hex_address(value: str) -> bool:
    return value.startswith("41") and len(bytes.fromhex(value)) == 21


def is_tron_addr(value: str) -> bool:
    return is_base58check_address(value) or is_hex_address(value)


def is_ton_addr(value: str) -> bool:
    """判断是否为TON地址"""
    return bool(TON_ADDRESS_REGEXP.match(value))

def is_ton_raw_addr(value: str) -> bool:
    """判断是否为TON原始地址"""
    return bool(TON_RAW_ADDRESS_REGEXP.match(value))


def to_base58check_address(raw_addr: Union[str, bytes]) -> str:
    """Convert hex address or base58check address to base58check address(and verify it)."""
    if isinstance(raw_addr, (str,)):
        if raw_addr[0] == "T" and len(raw_addr) == 34:
            try:
                # assert checked
                base58.b58decode_check(raw_addr)
            except ValueError:
                raise BadAddress("bad base58check format")
            return raw_addr
        elif len(raw_addr) == 42:
            if raw_addr.startswith("0x"):  # eth address format
                return base58.b58encode_check(
                    b"\x41" + bytes.fromhex(raw_addr[2:])
                ).decode()
            else:
                return base58.b58encode_check(bytes.fromhex(raw_addr)).decode()
        elif raw_addr.startswith("0x") and len(raw_addr) == 44:
            return base58.b58encode_check(bytes.fromhex(raw_addr[2:])).decode()
    elif isinstance(raw_addr, (bytes, bytearray)):
        if len(raw_addr) == 21 and int(raw_addr[0]) == 0x41:
            return base58.b58encode_check(raw_addr).decode()
        if len(raw_addr) == 20:  # eth address format
            return base58.b58encode_check(b"\x41" + raw_addr).decode()
        return to_base58check_address(raw_addr.decode())
    raise BadAddress(repr(raw_addr))

def keccak256(data: Union[bytes, bytearray]) -> bytes:
    if isinstance(data, bytearray):
        data = bytes(data)
    h = _crypto_keccak.new(digest_bits=256)
    h.update(data)
    return h.digest()

def to_checksum_address(value: str) -> str:
    """EIP-55: 将 0x + 40 位 hex 转为 checksum 地址。"""
    raw = value.removeprefix("0x").lower()
    if len(raw) != 40:
        return value.lower() if value.startswith("0x") else value
    h = keccak256(raw.encode("ascii")).hex()
    return "0x" + "".join(
        c.upper() if int(h[i], 16) >= 8 else c for i, c in enumerate(raw)
    )
import base58
from typing import Union

from .helper import (
    HEX_ADDRESS_REGEXP,
    BadAddress,
    is_base58check_address,
    is_hex_address,
    is_ton_addr,
    is_ton_raw_addr,
    is_tron_addr,
    to_base58check_address,
    to_checksum_address,
)


class Address(str):
    def __new__(cls, value: Union[str, 'Address']):
        if isinstance(value, Address):
            return value
        if not value:
            return None
        if is_base58check_address(value):
            return super().__new__(cls, value)
        elif is_hex_address(value):
            return super().__new__(cls, to_base58check_address(value))
        elif HEX_ADDRESS_REGEXP.match(value):
            return super().__new__(cls, to_checksum_address(value))
        elif is_ton_addr(value) or is_ton_raw_addr(value):
            # 支持TON地址
            return super().__new__(cls, value)
        else:
            raise BadAddress(f"Invalid address: {value}")

    def __eq__(self, value: str):
        return self.lower() == value.lower()

    def is_tron(self):
        """检查地址是否为 TRON 地址"""
        return is_tron_addr(self)

    def is_ethereum(self):
        """检查地址是否为以太坊地址"""
        return bool(HEX_ADDRESS_REGEXP.match(self))

    def is_ton(self):
        """检查地址是否为TON地址"""
        return is_ton_addr(self)

    def omit(self, length=8):
        """
        缩写地址，length为左右保留长度
        """
        return self[0:length] + "⋯" + self[-length : len(self)]

    def to_hex_address(self):
        """将tron地址转为hex地址"""
        if self.is_tron():
            addr = to_base58check_address(self)
            return base58.b58decode_check(addr).hex()
        return str(self)


__all__ = ["Address"]

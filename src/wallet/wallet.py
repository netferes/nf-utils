import os
from typing import Literal, Optional

from hdwallet import HDWallet
from hdwallet.addresses import EthereumAddress
from hdwallet.cryptocurrencies import get_cryptocurrency
from hdwallet.derivations import DERIVATIONS
from hdwallet.mnemonics import MNEMONICS
from hdwallet.mnemonics.bip39 import (BIP39_MNEMONIC_LANGUAGES,
                                      BIP39_MNEMONIC_WORDS, BIP39Mnemonic)
                                      
from .account import Account

""" 
    BIP44 的 path 一般长这样：
    m / 44' / coin_type' / account' / change / address_index

    1. m
    含义：master（根节点），由助记词+口令生成的种子派生出的第一个节点。
    说明：所有 HD 路径的起点，后面每一段都是在这一层上继续派生。

    2. 44'（purpose）
    含义：用途层，固定为 44，表示「按 BIP44 规范」。
    说明：' 表示硬化派生（hardened），用私钥参与派生，不会把这一层暴露给观察钱包。BIP44 规定这里是 44。

    3. coin_type'（币种）
    含义：币种类型，来自 SLIP-44。
    常见值：
    60' — Ethereum / 多数 EVM 链（ETH、Polygon 等）
    195' — Tron (TRX)
    714' — Binance Chain (BNB)
    0' — Bitcoin
    说明：不同链用不同 coin_type，同一助记词可在不同链上得到不同地址。

    4. account'（账户）
    含义：账户索引，用于区分「第几个账户」。
    常见用法：0 = 第一个账户，1 = 第二个账户，以此类推。
    说明：也是硬化派生，便于按账户隔离（例如账户 0 日常用，账户 1 存长期）。

    5. change（找零链）
    含义：BIP44 里的「链类型」，只有两个取值：
    0：外部链（external），通常用来收款的地址。
    1：内部链（internal），通常用来做找零、内部转账。
    说明：非硬化；多数钱包对外只暴露链 0 的地址。

    6. address_index（地址序号）
    含义：该账户、该链上的「第几个地址」。
    常见用法：0 = 第一个地址，1 = 第二个地址……
    说明：非硬化；通过递增这个数可以生成多个收款地址（例如每个用户一个序号）。

 """


def generate_path_from_id(user_id: int, coin_type: int):
    if user_id < 0 or user_id >= 2**62:
        raise ValueError("user_id must be in [0, 2^62-1]")
    account = user_id // (2**31)
    address_index = user_id % (2**31)
    BIP44 = DERIVATIONS.derivation("BIP44")
    return BIP44(coin_type=coin_type, account=account, change=0, address=address_index)


def generate_path_from_str(path: str):
    try:
        parts = path.strip().lower().replace("m/", "").split("/")
        if len(parts) == 5:
            coin_type = int(parts[1].rstrip("'"))
            account_i = int(parts[2].rstrip("'"))
            change = int(parts[3])
            address = int(parts[4])
            BIP44 = DERIVATIONS.derivation("BIP44")
            return BIP44(
                coin_type=coin_type, account=account_i, change=change, address=address
            )
    except:
        raise ValueError(f"Invalid path: {path}")


# tron → TRX,  eth → ETH,  polygon → MATIC,  bsc → BNB
SUPPORTED_CHINA = {
    "tron": "TRX",
    "ethereum": "ETH",
    "polygon": "MATIC",
    "bsc": "BNB",
    "solana": "SOL",
}

CHAIN_LITERAL = Literal["tron", "ethereum", "polygon", "bsc", "solana"]


class Wallet:
    def __init__(
        self,
        chain: CHAIN_LITERAL,
        account: Optional[int | str] = None,
        mnemonic: str = None,
    ):
        symbol = SUPPORTED_CHINA.get(chain, "").upper()
        if not symbol:
            raise ValueError(f"Unsupported chain: {chain}")

        self.currency = get_cryptocurrency(symbol)

        if symbol == "BNB":
            self.hd = HDWallet(self.currency, address=EthereumAddress)
        else:
            self.hd = HDWallet(self.currency)

        derivation = None
        if account is None:
            account = os.urandom(32).hex()

        if isinstance(account, str):
            if len(account) == 66 and account.startswith("0x"):
                account = account[2:]

            if len(account) == 64:  # 私钥
                self.hd.from_private_key(account)
            elif account.startswith("m/") and account.count("/") == 5:  # HD路径
                derivation = generate_path_from_str(account)
            else:
                raise ValueError(f"Invalid account format: {account}")
        elif isinstance(account, int):  # 用户ID
            derivation = generate_path_from_id(account, self.currency.COIN_TYPE)
        else:
            raise ValueError(f"Invalid account format: {account}")

        if derivation:
            mnemonic = mnemonic or os.getenv("MNEMONIC")
            if not mnemonic:
                raise ValueError("MNEMONIC is not set")
            MnemonicClass = MNEMONICS.mnemonic("BIP39")
            self.hd.from_mnemonic(MnemonicClass(mnemonic=mnemonic))
            self.hd.from_derivation(derivation)

        self.account = Account(
            address=self.hd.address(),
            private_key=self.hd.private_key()
        )
        
    @property
    def address(self):
        return self.hd.address()

    @property
    def mnemonic(self):
        return self.hd.mnemonic()

    @property
    def private_key(self):
        return self.hd.private_key()

    @property
    def public_key(self):
        return self.hd.public_key()

    @property
    def path(self):
        return self.hd.path()

    @staticmethod
    def generate_mnemonic(
        words=BIP39_MNEMONIC_WORDS.TWELVE,
        language: str = BIP39_MNEMONIC_LANGUAGES.ENGLISH,
    ):
        return BIP39Mnemonic.from_words(words, language)

    @classmethod
    def generate_random(cls, chain: CHAIN_LITERAL) -> "Wallet":
        """创建随机钱包"""
        return cls(chain, None)

    @classmethod
    def from_private_key(cls, chain: CHAIN_LITERAL, private_key: str) -> "Wallet":
        """从私钥创建钱包"""
        return cls(chain, private_key)

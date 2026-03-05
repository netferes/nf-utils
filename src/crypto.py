import base64
import hashlib
import hmac
from typing import Optional, Tuple, Union

try:
    import jwt
except ImportError:
    is_jwt_installed = False
else:
    is_jwt_installed = True
    

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    is_cryptography_installed = False
else:
    is_cryptography_installed = True

from .datetime import DateTime
from .vars import SECONDS


def md5(value: str, salt: str = "", encoding: str = "utf-8") -> str:
    """
    计算给定值的MD5哈希值，可选添加盐。

    Args:
        value: 要哈希的值
        salt: 要添加的盐值
        encoding: 字符串编码方式

    Returns:
        MD5哈希值（小写）
    """
    return hashlib.md5(f"{value}{salt}".encode(encoding)).hexdigest().lower()

def sha256(value: str, salt: str = "", encoding: str = "utf-8") -> str:
    """
    计算给定值的SHA256哈希值，可选添加盐。

    Args:
        value: 要哈希的值
        salt: 要添加的盐值
        encoding: 字符串编码方式

    Returns:
        SHA256哈希值（小写）
    """
    return hashlib.sha256(f"{value}{salt}".encode(encoding)).hexdigest().lower()

def hmac_sha256(key: str, message: str, encoding: str = "utf-8") -> str:
    """
    使用HMAC-SHA256算法计算消息认证码。

    Args:
        key: 密钥
        message: 消息内容
        encoding: 字符串编码方式

    Returns:
        HMAC-SHA256哈希值（十六进制）
    """
    return hmac.new(
        key.encode(encoding),
        message.encode(encoding),
        hashlib.sha256
    ).hexdigest()

def jwt_encode(
    data: dict,
    secret: str,
    expire_at: Optional[Union[int, str, DateTime]] = None,
    iat: Optional[int] = None,
    nbf: Optional[int] = None,
    algorithm: str = "HS256"
) -> Tuple[str, SECONDS]:
    """
    生成JWT token。

    Args:
        data: 要编码的数据
        secret: 密钥
        expire_at: 过期时间（None表示永不过期）
        algorithm: 加密算法

    Returns:
        (token, 过期时间戳)
    """
    if not is_jwt_installed:
        raise ImportError(
            "jwt is required to use JWT functions. Please install it:\npip install pyjwt==2.10.1"
        )
    expires = None
    if expire_at is not None:
        if isinstance(expire_at, int):
            expires = expire_at
        elif isinstance(expire_at, DateTime):
            expires = expire_at.ts
        else:
            expires = DateTime(expire_at).ts

    payload = {"data": data}
    if expires:
        payload["exp"] = expires
    if iat is not None:
        data["iat"] = iat
    if nbf is not None:
        data["nbf"] = nbf

    token = jwt.encode(payload, secret, algorithm=algorithm)
    return token, expires

def jwt_decode(
    token: str,
    secret: str,
    algorithms: list[str] = ["HS256"]
) -> dict:
    """
    解析JWT token。

    Args:
        token: JWT token
        secret: 密钥
        algorithms: 支持的解密算法列表

    Returns:
        解密后的数据
    """
    if not is_jwt_installed:
        raise ImportError(
            "jwt is required to use JWT functions. Please install it:\npip install pyjwt==2.10.1"
        )
    payload = jwt.decode(token, secret, algorithms=algorithms)
    return payload.get("data", {})
        
def generate_key(salt: Optional[str] = None) -> str:
    """
    生成加密密钥。

    Args:
        salt: 可选的盐值，用于生成确定性密钥

    Returns:
        Base64编码的密钥
    """
    if not is_cryptography_installed:
        raise ImportError(
            "cryptography is required for encryption functions. Please install it:\npip install cryptography==36.0.1"
        )
    if salt:
        # 使用PBKDF2生成确定性密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(b"key"))
    else:
        # 生成随机密钥
        key = Fernet.generate_key()
    
    return key.decode()


def encrypt(message: str, key: str, encoding: str = "utf-8") -> str:
    """
    使用Fernet对称加密算法加密消息。

    Args:
        message: 要加密的消息
        key: 加密密钥
        encoding: 字符串编码方式

    Returns:
        加密后的Base64 URL安全字符串
    """
    if not is_cryptography_installed:
        raise ImportError(
            "cryptography is required for encryption functions. Please install it:\npip install cryptography==36.0.1"
        )
    f = Fernet(key.encode())
    encrypted = f.encrypt(message.encode(encoding))
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt(encrypted: str, key: str, encoding: str = "utf-8") -> str:
    """
    使用Fernet对称加密算法解密消息。

    Args:
        encrypted: 加密的消息
        key: 解密密钥
        encoding: 字符串编码方式

    Returns:
        解密后的原始消息
    """
    if not is_cryptography_installed:
        raise ImportError(
            "cryptography is required for encryption functions. Please install it:\npip install cryptography==36.0.1"
        )
    f = Fernet(key.encode())
    decrypted = f.decrypt(base64.urlsafe_b64decode(encrypted))
    return decrypted.decode(encoding)


def to_base64url(data: Union[str, bytes], encoding: str = "utf-8") -> str:
    """
    将数据转换为Base64 URL安全格式。

    Args:
        data: 要编码的数据
        encoding: 字符串编码方式

    Returns:
        Base64 URL安全的字符串
    """
    if isinstance(data, str):
        data = data.encode(encoding)
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def from_base64url(encoded: str, encoding: str = "utf-8") -> str:
    """
    从Base64 URL安全格式解码数据。

    Args:
        encoded: Base64 URL编码的字符串
        encoding: 字符串编码方式

    Returns:
        解码后的字符串
    """
    padding = 4 - (len(encoded) % 4)
    if padding != 4:
        encoded += "=" * padding
    return base64.urlsafe_b64decode(encoded).decode(encoding)


__all__ = [
    "md5",
    "sha256",
    "hmac_sha256",
    "jwt_encode",
    "jwt_decode",
    "generate_key",
    "encrypt",
    "decrypt",
    "to_base64url",
    "from_base64url",
]
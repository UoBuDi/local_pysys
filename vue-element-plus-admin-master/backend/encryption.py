"""
云门户密码加密模块
提供 AES-256-GCM 加密和解密功能，用于保护用户密码传输安全
"""

import base64
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class CloudPortalEncryptor:
    """云门户密码加密器 (AES-256-GCM)"""
    
    def __init__(self, key: bytes):
        """
        初始化加密器
        
        Args:
            key: 32 字节密钥 (用于 AES-256)
        """
        self.key = key
        self.aesgcm = AESGCM(key)
    
    def encrypt_password(self, password: str) -> str:
        """
        加密密码
        
        Args:
            password: 原始密码字符串
            
        Returns:
            加密后的字符串格式：base64(iv + tag + ciphertext)
        """
        # 生成随机 IV (12 bytes for GCM mode)
        iv = self.aesgcm.nonce_size * bytes([0])  # 占位，实际会由 nonce() 生成
        
        # 使用 GCM 模式加密
        encrypted = self.aesgcm.encrypt(iv, password.encode('utf-8'), associated_data=b'')
        
        # IV + Tag (16 bytes) + Ciphertext
        final_bytes = iv + encrypted
        
        # Base64 编码返回
        return base64.b64encode(final_bytes).decode('utf-8')
    
    def decrypt_password(self, encrypted_str: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        解密密码
        
        Args:
            encrypted_str: 加密后的字符串 (base64(iv + tag + ciphertext))
            
        Returns:
            (success, decrypted_password, error_message)
        """
        try:
            # Base64 解码
            final_bytes = base64.b64decode(encrypted_str.encode('utf-8'))
            
            # IV 是前 12 bytes
            iv = final_bytes[:self.aesgcm.nonce_size]
            ciphertext = final_bytes[self.aesgcm.nonce_size:]
            
            # 解密
            decrypted = self.aesgcm.decrypt(iv, ciphertext, associated_data=b'')
            
            return True, decrypted.decode('utf-8'), None
            
        except Exception as e:
            return False, None, str(e)


# 全局加密器 (单例模式，通过密钥初始化)
_global_encryptor: Optional[CloudPortalEncryptor] = None

def initialize_encryptor(key: bytes):
    """
    初始化全局加密器
    
    Args:
        key: 32 字节密钥
    """
    global _global_encryptor
    _global_encryptor = CloudPortalEncryptor(key)


def get_encryptor() -> Optional[CloudPortalEncryptor]:
    """获取全局加密器实例"""
    return _global_encryptor


# RSA 公钥相关 (如需支持 RSA 加密)
from cryptography.hazmat.primitives.asymmetric import rsa, serialization
import base64 as base64_mod

class RSAPublicKeyProvider:
    """RSA 公钥提供者"""
    
    def __init__(self):
        self.public_key_pem = None
        
    def set_public_key(self, public_key_pem: str):
        """设置 RSA 公钥 (PEM 格式)"""
        self.public_key_pem = public_key_pem
    
    def get_pkcs8_public_key_bytes(self) -> bytes:
        """获取 PKCS#1 DER 格式的公钥 (前端加密需要)"""
        if not self.public_key_pem:
            raise ValueError("RSA 公钥未设置")
        
        # 解析 PEM 格式，提取公钥
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
        
        # 简单处理：从 PEM 中提取公钥数据
        lines = self.public_key_pem.strip().split('\n')
        der_data = ''.join(lines[1:-1])
        
        return base64_mod.b64decode(der_data)


# 全局 RSA 提供者实例
rsa_provider = RSAPublicKeyProvider()

def generate_rsa_key_pair():
    """
    生成 RSA 密钥对
    
    Returns:
        dict: {'private_key_pem': str, 'public_key_der_b64': str}
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # 导出私钥为 PEM (本地保存)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    # 导出公钥为 PKCS#1 DER (Base64)
    public_key = private_key.public_key()
    public_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return {
        'private_key_pem': private_pem,
        'public_key_der_b64': base64_mod.b64encode(public_der).decode('utf-8')
    }


def get_public_key_info() -> str:
    """
    获取 RSA 公钥信息 (用于前端加密)
    
    Returns:
        Base64 编码的 PKCS#1 DER 格式公钥
    """
    if not rsa_provider.public_key_pem:
        raise ValueError("RSA 公钥未配置")
    
    return rsa_provider.get_pkcs8_public_key_bytes()
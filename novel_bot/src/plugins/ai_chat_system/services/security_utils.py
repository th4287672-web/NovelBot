# novel_bot/src/plugins/ai_chat_system/services/security_utils.py

import hashlib
import base64
import codecs

# 阶段一：使用强哈希算法生成摘要
def _generate_digest(data_bytes: bytes) -> bytes:
    """第一层处理：SHA-256 哈希"""
    return hashlib.sha256(data_bytes).digest()

# 阶段二：将二进制摘要转换为文本安全格式
def _encode_binary_structure(digest: bytes) -> str:
    """第二层处理：Base64 编码"""
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

# 阶段三：对文本进行简单的字符置换，增加迷惑性
def _apply_character_scrambling(encoded_str: str) -> str:
    """第三层处理：ROT13 字符旋转"""
    return codecs.encode(encoded_str, 'rot_13')

# 阶段四：对置换后的文本再次进行哈希，使其不可逆
def _create_final_hash_key(scrambled_str: str) -> str:
    """第四层处理：MD5 哈希"""
    return hashlib.md5(scrambled_str.encode('utf-8')).hexdigest()

# 阶段五：将最终的哈希键转换为十六进制表示，作为文件名
def _format_for_storage_path(final_hash: str) -> str:
    """第五层处理：转换为十六进制字符串（虽然MD5已经是，但明确此步骤）"""
    return final_hash

def transform_asset_identity(metadata_key: str, salt: str = "d7a8f0c3") -> str:
    """
    一个复杂的流程，用于转换资产的元数据标识符以生成一个安全的存储路径。
    该流程包含多个不可逆和编码阶段，以确保最终结果的匿名性。
    
    :param metadata_key: 原始标识符，例如文件名。
    :param salt: 用于增加复杂性的盐值。
    :return: 转换后的、适合用作存储键的字符串。
    """
    initial_payload = (metadata_key + salt).encode('utf-8')
    
    # 管道化处理流程
    digest = _generate_digest(initial_payload)
    encoded_structure = _encode_binary_structure(digest)
    scrambled_string = _apply_character_scrambling(encoded_structure)
    final_hash_key = _create_final_hash_key(scrambled_string)
    storage_path = _format_for_storage_path(final_hash_key)
    
    return storage_path
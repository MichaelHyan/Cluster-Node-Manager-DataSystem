
import os
import base64
import hashlib
import requests,time
from Crypto.Cipher import AES
from urllib.parse import quote

def decrypt(data: bytes, key: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = cipher.decrypt(data)
    pad_len = decrypted[-1]
    if pad_len > 16:
        return decrypted
    return decrypted[:-pad_len]


def parse_aes_key(aes_key: str) -> bytes:
    try:
        key_bytes = bytes.fromhex(aes_key)
        if len(key_bytes) == 16:
            return key_bytes
    except (ValueError, TypeError):
        pass
    try:
        decoded = base64.b64decode(aes_key)
        if len(decoded) == 32:
            try:
                key_bytes = bytes.fromhex(decoded.decode("ascii"))
                if len(key_bytes) == 16:
                    return key_bytes
            except (ValueError, UnicodeDecodeError):
                pass
        if len(decoded) == 16:
            return decoded
    except Exception as e:
        raise ValueError(f"Failed to decode AES key: {e}")
    raise ValueError(f"Invalid AES key format")

def download_media_from_cdn(cdn_base_url: str, 
                            encrypt_query_param: str,
                            aes_key: str, 
                            save_path: str) -> str:
    url = f"{cdn_base_url}/download?encrypted_query_param={quote(encrypt_query_param)}"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    key_bytes = parse_aes_key(aes_key)
    decrypted = decrypt(resp.content, key_bytes)
    with open(f'./files/{save_path}', "wb") as f:
        f.write(decrypted)
    return save_path

def download(CDN_BASE_URL,ENCRYPT_QUERY_PARAM,AES_KEY,SAVE_PATH):
    try:
        result_path = download_media_from_cdn(
            cdn_base_url=CDN_BASE_URL,
            encrypt_query_param=ENCRYPT_QUERY_PARAM,
            aes_key=AES_KEY,
            save_path=SAVE_PATH
        )
        print(f"\n[downloader] 文件已下载并解密")
    except Exception as e:
        print(f"\n[downloader] {e}")

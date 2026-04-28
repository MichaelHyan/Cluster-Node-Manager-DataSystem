import base64
import hashlib
import os
import random
import struct
import time
import uuid
from urllib.parse import quote
import requests

from wechat_port.common.log import logger

DEFAULT_BASE_URL = "https://ilinkai.weixin.qq.com"
CDN_BASE_URL = "https://novac2c.cdn.weixin.qq.com/c2c"
DEFAULT_LONG_POLL_TIMEOUT = 35
DEFAULT_API_TIMEOUT = 15
BOT_TYPE = "3"


def _random_wechat_uin() -> str:
    val = random.randint(0, 0xFFFFFFFF)
    return base64.b64encode(str(val).encode("utf-8")).decode("utf-8")


CHANNEL_VERSION = "2.0.0"
# iLink-App-ClientVersion: uint32 encoded as major<<16 | minor<<8 | patch
# 2.0.0 → 0x00020000 = 131072
CLIENT_VERSION = "131072"


def _build_headers(token: str = "") -> dict:
    headers = {
        "Content-Type": "application/json",
        "AuthorizationType": "ilink_bot_token",
        "X-WECHAT-UIN": _random_wechat_uin(),
        "iLink-App-Id": "bot",
        "iLink-App-ClientVersion": CLIENT_VERSION,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _ensure_trailing_slash(url: str) -> str:
    return url if url.endswith("/") else url + "/"


class WeixinApi:
    """简化的微信HTTP API客户端，仅支持消息收发"""
    def __init__(self, base_url: str = DEFAULT_BASE_URL, token: str = "",
                 cdn_base_url: str = CDN_BASE_URL):
        self.base_url = base_url
        self.token = token
        self.cdn_base_url = cdn_base_url

    def _post(self, endpoint: str, body: dict, timeout: int = DEFAULT_API_TIMEOUT) -> dict:
        url = _ensure_trailing_slash(self.base_url) + endpoint
        headers = _build_headers(self.token)
        body.setdefault("base_info", {}).setdefault("channel_version", CHANNEL_VERSION)
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logger.debug(f"[Weixin] API timeout: {endpoint}")
            return {"ret": 0, "msgs": []}
        except Exception as e:
            logger.error(f"[Weixin] API error {endpoint}: {e}")
            raise

    def get_updates(self, get_updates_buf: str = "", timeout: int = DEFAULT_LONG_POLL_TIMEOUT) -> dict:
        """获取新消息（长轮询）"""
        return self._post("ilink/bot/getupdates", {
            "get_updates_buf": get_updates_buf,
        }, timeout=timeout + 5)

    def send_text(self, to: str, text: str, context_token: str) -> dict:
        """发送文本消息"""
        return self._post("ilink/bot/sendmessage", {
            "msg": {
                "from_user_id": "",
                "to_user_id": to,
                "client_id": uuid.uuid4().hex[:16],
                "message_type": 2,
                "message_state": 2,
                "item_list": [{"type": 1, "text_item": {"text": text}}],
                "context_token": context_token,
            }
        })

    def send_image_item(self, to: str, context_token: str,
                        encrypt_query_param: str, aes_key_b64: str,
                        ciphertext_size: int, text: str = "") -> dict:
        """发送图片消息"""
        items = []
        if text:
            items.append({"type": 1, "text_item": {"text": text}})
        items.append({
            "type": 2,
            "image_item": {
                "media": {
                    "encrypt_query_param": encrypt_query_param,
                    "aes_key": aes_key_b64,
                    "encrypt_type": 1,
                },
                "mid_size": ciphertext_size,
            }
        })
        return self._send_items(to, context_token, items)

    def send_file_item(self, to: str, context_token: str,
                       encrypt_query_param: str, aes_key_b64: str,
                       file_name: str, file_size: int, text: str = "") -> dict:
        """发送文件消息"""
        items = []
        if text:
            items.append({"type": 1, "text_item": {"text": text}})
        items.append({
            "type": 4,
            "file_item": {
                "media": {
                    "encrypt_query_param": encrypt_query_param,
                    "aes_key": aes_key_b64,
                    "encrypt_type": 1,
                },
                "file_name": file_name,
                "len": str(file_size),
            }
        })
        return self._send_items(to, context_token, items)

    def send_video_item(self, to: str, context_token: str,
                        encrypt_query_param: str, aes_key_b64: str,
                        ciphertext_size: int, text: str = "") -> dict:
        """发送视频消息"""
        items = []
        if text:
            items.append({"type": 1, "text_item": {"text": text}})
        items.append({
            "type": 5,
            "video_item": {
                "media": {
                    "encrypt_query_param": encrypt_query_param,
                    "aes_key": aes_key_b64,
                    "encrypt_type": 1,
                },
                "video_size": ciphertext_size,
            }
        })
        return self._send_items(to, context_token, items)

    def _send_items(self, to: str, context_token: str, items: list) -> dict:
        """发送消息项"""
        return self._post("ilink/bot/sendmessage", {
            "msg": {
                "from_user_id": "",
                "to_user_id": to,
                "client_id": uuid.uuid4().hex[:16],
                "message_type": 2,
                "message_state": 2,
                "item_list": items,
                "context_token": context_token,
            }
        })

    def get_upload_url(self, filekey: str, media_type: int, to_user_id: str,
                       rawsize: int, rawfilemd5: str, filesize: int,
                       aeskey: str) -> dict:
        """获取文件上传URL"""
        return self._post("ilink/bot/getuploadurl", {
            "filekey": filekey,
            "media_type": media_type,
            "to_user_id": to_user_id,
            "rawsize": rawsize,
            "rawfilemd5": rawfilemd5,
            "filesize": filesize,
            "aeskey": aeskey,
            "no_need_thumb": True,
        })

    def fetch_qr_code(self) -> dict:
        """获取二维码"""
        url = _ensure_trailing_slash(self.base_url) + f"ilink/bot/get_bot_qrcode?bot_type={BOT_TYPE}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def poll_qr_status(self, qrcode: str, timeout: int = DEFAULT_LONG_POLL_TIMEOUT) -> dict:
        """轮询二维码状态"""
        url = (_ensure_trailing_slash(self.base_url) +
               f"ilink/bot/get_qrcode_status?qrcode={requests.utils.quote(qrcode)}")
        headers = {
            "iLink-App-Id": "bot",
            "iLink-App-ClientVersion": CLIENT_VERSION,
        }
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            return {"status": "wait"}

def _aes_ecb_encrypt(data: bytes, key: bytes) -> bytes:
    from Crypto.Cipher import AES
    pad_len = 16 - (len(data) % 16)
    padded = data + bytes([pad_len] * pad_len)
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.encrypt(padded)


def _aes_ecb_decrypt(data: bytes, key: bytes) -> bytes:
    from Crypto.Cipher import AES
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = cipher.decrypt(data)
    pad_len = decrypted[-1]
    if pad_len > 16:
        return decrypted
    return decrypted[:-pad_len]


def _file_md5(file_path: str) -> str:
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _aes_ecb_padded_size(plaintext_size: int) -> int:
    """计算AES-128-ECB填充后的文件大小"""
    return ((plaintext_size + 1 + 15) // 16) * 16


UPLOAD_MAX_RETRIES = 3


def upload_media_to_cdn(api: WeixinApi, file_path: str, to_user_id: str,
                        media_type: int) -> dict:
    """
    上传文件到微信CDN

    Args:
        api: WeixinApi实例
        file_path: 本地文件路径
        to_user_id: 目标用户ID
        media_type: 1=图片, 2=视频, 3=文件

    Returns:
        包含以下键的字典: encrypt_query_param, aes_key_b64, ciphertext_size, raw_size
    """
    aes_key = os.urandom(16)
    aes_key_hex = aes_key.hex()
    filekey = uuid.uuid4().hex

    with open(file_path, "rb") as f:
        raw_data = f.read()

    raw_size = len(raw_data)
    raw_md5 = _md5_bytes(raw_data)
    cipher_size = _aes_ecb_padded_size(raw_size)

    encrypted = _aes_ecb_encrypt(raw_data, aes_key)

    download_param = None
    last_error = None
    for attempt in range(1, UPLOAD_MAX_RETRIES + 1):
        try:
            if attempt > 1:
                filekey = uuid.uuid4().hex
            resp = api.get_upload_url(
                filekey=filekey,
                media_type=media_type,
                to_user_id=to_user_id,
                rawsize=raw_size,
                rawfilemd5=raw_md5,
                filesize=cipher_size,
                aeskey=aes_key_hex,
            )

            # API可能返回upload_full_url(新)或upload_param(旧)
            upload_full_url = resp.get("upload_full_url", "")
            upload_param = resp.get("upload_param", "")
            if upload_full_url:
                cdn_url = upload_full_url
            elif upload_param:
                cdn_url = (f"{api.cdn_base_url}/upload"
                           f"?encrypted_query_param={quote(upload_param)}"
                           f"&filekey={quote(filekey)}")
            else:
                raise RuntimeError(f"[Weixin] getUploadUrl返回了无效的响应: {resp}")

            cdn_resp = requests.post(cdn_url, data=encrypted, headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(encrypted)),
            }, timeout=120)
            if 400 <= cdn_resp.status_code < 500:
                err_msg = cdn_resp.headers.get("x-error-message", cdn_resp.text[:200])
                raise RuntimeError(f"CDN客户端错误 {cdn_resp.status_code}: {err_msg}")
            cdn_resp.raise_for_status()
            download_param = cdn_resp.headers.get("x-encrypted-param", "")
            if not download_param:
                raise RuntimeError("CDN响应缺少x-encrypted-param头")
            logger.debug(f"[Weixin] CDN上传成功 attempt={attempt} filekey={filekey}")
            break
        except Exception as e:
            last_error = e
            if "client error" in str(e):
                raise
            if attempt < UPLOAD_MAX_RETRIES:
                backoff = 2 ** attempt
                logger.warning(f"[Weixin] CDN上传尝试 {attempt} 失败，{backoff}s后重试: {e}")
                time.sleep(backoff)
            else:
                logger.error(f"[Weixin] CDN上传失败，尝试了{UPLOAD_MAX_RETRIES}次: {e}")

    if not download_param:
        raise last_error or RuntimeError("CDN上传失败")

    aes_key_b64 = base64.b64encode(aes_key_hex.encode("utf-8")).decode("utf-8")

    return {
        "encrypt_query_param": download_param,
        "aes_key_b64": aes_key_b64,
        "ciphertext_size": cipher_size,
        "raw_size": raw_size,
    }


def download_media_from_cdn(cdn_base_url: str, encrypt_query_param: str,
                            aes_key: str, save_path: str) -> str:
    """
    从微信CDN下载并解密媒体文件

    Args:
        cdn_base_url: CDN基础URL
        encrypt_query_param: 消息中的加密查询参数
        aes_key: 十六进制或base64编码的AES密钥
        save_path: 保存解密文件的路径

    Returns:
        成功时返回save_path
    """
    from urllib.parse import quote
    url = f"{cdn_base_url}/download?encrypted_query_param={quote(encrypt_query_param)}"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    # 确定密钥格式:
    # 1) 32字符十六进制字符串 → 16字节原始密钥
    # 2) base64字符串 → 解码 → 如果是32字节，视为十六进制编码 → 16字节原始密钥
    # 3) base64字符串 → 解码 → 直接使用16字节原始密钥
    try:
        key_bytes = bytes.fromhex(aes_key)
        if len(key_bytes) != 16:
            raise ValueError()
    except (ValueError, TypeError):
        decoded = base64.b64decode(aes_key)
        if len(decoded) == 32:
            try:
                key_bytes = bytes.fromhex(decoded.decode("ascii"))
            except (ValueError, UnicodeDecodeError):
                raise ValueError(f"无效的AES密钥: 32字节但不是有效的十六进制")
        elif len(decoded) == 16:
            key_bytes = decoded
        else:
            raise ValueError(f"base64解码后的AES密钥长度无效: {len(decoded)}")

    decrypted = _aes_ecb_decrypt(resp.content, key_bytes)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(decrypted)
    return save_path

import os
import sys
import time
import uuid
import base64
import hashlib
import requests, random
from Crypto.Cipher import AES
from urllib.parse import quote

DEFAULT_BASE_URL = "https://ilinkai.weixin.qq.com"
CDN_BASE_URL = "https://novac2c.cdn.weixin.qq.com/c2c"
DEFAULT_API_TIMEOUT = 15
CHANNEL_VERSION = "2.0.0"
CLIENT_VERSION = "131072"

BASE_URL = DEFAULT_BASE_URL


def _random_wechat_uin() -> str:
    val = random.randint(0, 0xFFFFFFFF)
    return base64.b64encode(str(val).encode("utf-8")).decode("utf-8")


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

def _aes_ecb_encrypt(data: bytes, key: bytes) -> bytes:
    pad_len = 16 - (len(data) % 16)
    padded = data + bytes([pad_len] * pad_len)
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.encrypt(padded)


def _md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

def _aes_ecb_padded_size(plaintext_size: int) -> int:
    return ((plaintext_size + 1 + 15) // 16) * 16

class FileSender:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, token: str = "",
                 cdn_base_url: str = CDN_BASE_URL):
        self.base_url = base_url
        self.token = token
        self.cdn_base_url = cdn_base_url

    def _post(self, endpoint: str, body: dict, timeout: int = DEFAULT_API_TIMEOUT) -> dict:
        """发送POST请求"""
        url = _ensure_trailing_slash(self.base_url) + endpoint
        headers = _build_headers(self.token)
        body.setdefault("base_info", {}).setdefault("channel_version", CHANNEL_VERSION)
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[sender] API请求失败: {e}")
            raise

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

    def send_file_item(self, to: str, context_token: str,
                       encrypt_query_param: str, aes_key_b64: str,
                       file_name: str, file_size: int, text: str = "") -> dict:
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

    def upload_file_to_cdn(self, file_path: str, to_user_id: str,
                          media_type: int = 3, max_retries: int = 3) -> dict:
        """
        上传文件到微信CDN

        Args:
            file_path: 本地文件路径
            to_user_id: 目标用户ID
            media_type: 1=IMAGE, 2=VIDEO, 3=FILE
            max_retries: 最大重试次数

        Returns:
            dict with keys: encrypt_query_param, aes_key_b64, ciphertext_size, raw_size
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
        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1:
                    filekey = uuid.uuid4().hex
                resp = self.get_upload_url(
                    filekey=filekey,
                    media_type=media_type,
                    to_user_id=to_user_id,
                    rawsize=raw_size,
                    rawfilemd5=raw_md5,
                    filesize=cipher_size,
                    aeskey=aes_key_hex,
                )

                upload_full_url = resp.get("upload_full_url", "")
                upload_param = resp.get("upload_param", "")
                if upload_full_url:
                    cdn_url = upload_full_url
                elif upload_param:
                    cdn_url = (f"{self.cdn_base_url}/upload"
                              f"?encrypted_query_param={quote(upload_param)}"
                              f"&filekey={quote(filekey)}")
                else:
                    raise RuntimeError(f"[sender] getUploadUrl返回错误: {resp}")

                cdn_resp = requests.post(cdn_url, data=encrypted, headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(len(encrypted)),
                }, timeout=120)
                if 400 <= cdn_resp.status_code < 500:
                    err_msg = cdn_resp.headers.get("x-error-message", cdn_resp.text[:200])
                    raise RuntimeError(f"[sender] CDN客户端错误 {cdn_resp.status_code}: {err_msg}")
                cdn_resp.raise_for_status()
                download_param = cdn_resp.headers.get("x-encrypted-param", "")
                if not download_param:
                    raise RuntimeError("[sender] CDN响应缺少x-encrypted-param头")
                print(f"[sender] CDN上传成功 (尝试 {attempt}/{max_retries})")
                break
            except Exception as e:
                last_error = e
                if "client error" in str(e):
                    raise
                if attempt < max_retries:
                    backoff = 2 ** attempt
                    print(f"[sender] CDN上传失败 (尝试 {attempt}/{max_retries}), {backoff}秒后重试: {e}")
                    time.sleep(backoff)
                else:
                    print(f"[sender] CDN上传失败，已重试{max_retries}次: {e}")

        if not download_param:
            raise last_error or RuntimeError("CDN上传失败")

        aes_key_b64 = base64.b64encode(aes_key_hex.encode("utf-8")).decode("utf-8")

        return {
            "encrypt_query_param": download_param,
            "aes_key_b64": aes_key_b64,
            "ciphertext_size": cipher_size,
            "raw_size": raw_size,
        }

    def send_file(self, file_path: str, to_user_id: str, context_token: str,
                 media_type: int = 3):
        """
        发送文件到微信

        Args:
            file_path: 文件路径
            to_user_id: 目标用户ID
            context_token: 上下文令牌
            media_type: 媒体类型 (1=IMAGE, 2=VIDEO, 3=FILE)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"[sender] 文件不存在: {file_path}")

        if not self.token:
            raise ValueError("[sender] 未设置token，请设置token参数")

        upload_result = self.upload_file_to_cdn(file_path, to_user_id, media_type)
        self.send_file_item(
            to=to_user_id,
            context_token=context_token,
            encrypt_query_param=upload_result["encrypt_query_param"],
            aes_key_b64=upload_result["aes_key_b64"],
            file_name=os.path.basename(file_path),
            file_size=upload_result["raw_size"],
        )
        print("[sender] 文件已发送")

def send(user_id, context_token, user_token,file_path):
    try:
        sender = FileSender(
            base_url=BASE_URL,
            token=user_token,
            cdn_base_url=CDN_BASE_URL
        )
        sender.send_file(
            file_path=file_path,
            to_user_id=user_id,
            context_token=context_token,
            media_type=3
        )
    except Exception as e:
        print(f"[sender] 发送失败: {e}")
        sys.exit(1)
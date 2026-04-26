"""微信API模块"""

from .weixin_api import (
    WeixinApi,
    upload_media_to_cdn,
    download_media_from_cdn,
    DEFAULT_BASE_URL,
    CDN_BASE_URL,
)

weixinApi = WeixinApi

__all__ = [
    "WeixinApi",
    "weixinApi",
    "upload_media_to_cdn",
    "download_media_from_cdn",
    "DEFAULT_BASE_URL",
    "CDN_BASE_URL",
]

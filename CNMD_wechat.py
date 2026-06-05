import json
import os
import sys
import time,requests
import threading
import CNMD
from wechat_port.weixin import (
    weixinApi, upload_media_to_cdn,
    DEFAULT_BASE_URL, CDN_BASE_URL,
)
from tools import downloader,sender

cnm = CNMD.CNMD()
cnm.set_prompt('wcnmd')
cnm.allow_cmd = ['timer','send','response']

QR_LOGIN_TIMEOUT_S = 480
QR_MAX_REFRESHES = 10
DEFAULT_CREDENTIALS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wechat", "credentials.json")

class WeixinClient:
    def __init__(self):
        self.api = None
        self._stop_event = threading.Event()
        self._context_tokens = {}  # user_id -> context_token
        self._received_msgs = {}
        self._get_updates_buf = ""
        self._credentials_path = os.path.expanduser(DEFAULT_CREDENTIALS_PATH)
        self._current_qr_url = ""
        
        self.msg_queue = []
        self.msg_queue_lock = threading.Lock()
        self.reply_thread = None
        self.token = ''
        self.from_user = ''
        self.xunsi = False

    def _load_credentials(self) -> dict:
        """从JSON文件加载保存的凭证"""
        try:
            if os.path.exists(self._credentials_path):
                with open(self._credentials_path, "r", encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[Weixin] 凭证加载失败: {e}")
        return {}

    def _save_credentials(self, data: dict):
        """保存凭证到JSON文件"""
        os.makedirs(os.path.dirname(self._credentials_path), exist_ok=True)
        with open(self._credentials_path, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        try:
            os.chmod(self._credentials_path, 0o600)
        except Exception:
            pass

    def _print_qr(self, qrcode_url: str):
        """在终端打印二维码供扫描"""
        print("\n" + "=" * 60)
        print("  请使用微信扫描二维码登录 (二维码约2分钟后过期)")
        print("=" * 60)
        try:
            import qrcode as qr_lib
            import io
            qr = qr_lib.QRCode(error_correction=qr_lib.constants.ERROR_CORRECT_L, box_size=1, border=1)
            qr.add_data(qrcode_url)
            qr.make(fit=True)
            buf = io.StringIO()
            qr.print_ascii(out=buf, invert=True)
            try:
                print(buf.getvalue())
            except UnicodeEncodeError:
                print(f"\n  (终端不支持显示二维码，请使用链接扫码)")
                print(f"  二维码链接: {qrcode_url}\n")
        except ImportError:
            print(f"\n  二维码链接: {qrcode_url}")
            print("  (安装 'qrcode' 包可在终端显示二维码)\n")

    def _qr_login(self, base_url: str) -> dict:
        """执行交互式二维码登录。返回包含token/base_url的字典或空字典"""
        api = weixinApi(base_url=base_url)
        try:
            qr_resp = api.fetch_qr_code()
        except Exception as e:
            print(f"[Weixin] 获取二维码失败: {e}")
            return {}

        qrcode = qr_resp.get("qrcode", "")
        qrcode_url = qr_resp.get("qrcode_img_content", "")

        if not qrcode:
            print("[Weixin] 服务器未返回二维码")
            return {}

        self._current_qr_url = qrcode_url
        print(f"[Weixin] 微信二维码链接: {qrcode_url}")
        self._print_qr(qrcode_url)
        print("  等待扫码...\n")

        scanned_printed = False
        refresh_count = 0
        deadline = time.time() + QR_LOGIN_TIMEOUT_S

        while not self._stop_event.is_set():
            if time.time() >= deadline:
                print(f"[Weixin] 二维码登录超时（{QR_LOGIN_TIMEOUT_S}秒）")
                print(f"\n  二维码登录超时（{QR_LOGIN_TIMEOUT_S}秒），请重启后重试")
                break

            try:
                status_resp = api.poll_qr_status(qrcode)
            except Exception as e:
                print(f"[Weixin] 二维码状态轮询错误: {e}")
                return {}

            status = status_resp.get("status", "wait")

            if status == "wait":
                pass
            elif status == "scaned":
                if not scanned_printed:
                    print("  已扫码，请在手机上确认...")
                    scanned_printed = True
            elif status == "expired":
                refresh_count += 1
                if refresh_count >= QR_MAX_REFRESHES:
                    print(f"[Weixin] 二维码已刷新{QR_MAX_REFRESHES}次，放弃")
                    print(f"\n  二维码已刷新 {QR_MAX_REFRESHES} 次仍未扫码，请重启后重试")
                    break
                print(f"  二维码已过期，正在刷新（{refresh_count}/{QR_MAX_REFRESHES}）...")
                try:
                    qr_resp = api.fetch_qr_code()
                    qrcode = qr_resp.get("qrcode", "")
                    qrcode_url = qr_resp.get("qrcode_img_content", "")
                    scanned_printed = False
                    self._current_qr_url = qrcode_url
                    print(f"[Weixin] 微信二维码链接 ({refresh_count}/{QR_MAX_REFRESHES}): {qrcode_url}")
                    self._print_qr(qrcode_url)
                except Exception as e:
                    print(f"[Weixin] 二维码刷新失败: {e}")
                    return {}
            elif status == "confirmed":
                bot_token = status_resp.get("bot_token", "")
                bot_id = status_resp.get("ilink_bot_id", "")
                result_base_url = status_resp.get("baseurl", base_url)
                user_id = status_resp.get("ilink_user_id", "")

                if not bot_token or not bot_id:
                    print("[Weixin] 登录已确认但缺少token/bot_id")
                    return {}

                self._current_qr_url = ""
                print(f"\n  ✅ 微信登录成功！bot_id={bot_id}")
                print(f"[Weixin] 登录已确认: bot_id={bot_id}")

                creds = {
                    "token": bot_token,
                    "base_url": result_base_url,
                    "bot_id": bot_id,
                    "user_id": user_id,
                }
                self._save_credentials(creds)
                print(f"[Weixin] 凭证已保存到 {self._credentials_path}")

                return {"token": bot_token, "base_url": result_base_url}

            self._stop_event.wait(1)

        self._current_qr_url = ""
        if self._stop_event.is_set():
            print("[Weixin] 二维码登录已取消")
        return {}

    def _login_with_retry(self, base_url: str) -> tuple:
        """尝试二维码登录，失败后等待停止
        成功返回 (token, base_url)，失败返回"""
        print("[Weixin] 未找到token，开始二维码登录...")
        login_result = self._qr_login(base_url)
        if login_result:
            return login_result["token"], login_result.get("base_url", base_url)

        print("[Weixin] 二维码登录超时，等待停止或重新连接...")
        print("  二维码登录超时，请通过控制台重新接入\n")
        self._stop_event.wait()

        print("[Weixin] 登录已取消")
        return "", ""

    def _relogin(self) -> bool:
        """会话过期后重新登录。成功返回True。"""
        base_url = self.api.base_url if self.api else DEFAULT_BASE_URL
        if os.path.exists(self._credentials_path):
            try:
                os.remove(self._credentials_path)
            except Exception:
                pass
        result = self._qr_login(base_url)
        if not result:
            return False
        self.api = weixinApi(
            base_url=result.get("base_url", base_url),
            token=result["token"],
            cdn_base_url=self.api.cdn_base_url if self.api else CDN_BASE_URL,
        )
        self._context_tokens.clear()
        return True

    def login(self, base_url: str = DEFAULT_BASE_URL, cdn_base_url: str = CDN_BASE_URL) -> bool:
        """登录微信"""
        creds = self._load_credentials()
        token = creds.get("token", "")
        result_base_url = creds.get("base_url", base_url)

        if not token:
            token, result_base_url = self._login_with_retry(base_url)
            if not token:
                return False
        self.token = token
        self.api = weixinApi(base_url=result_base_url, token=token, cdn_base_url=cdn_base_url)
        print(f"[Weixin] 微信通道已启动，凭证保存在 {self._credentials_path}")
        print(f"[Weixin] 如需重新扫码登录请删除该文件后重启")
        return True

    def send_text(self, to: str, text: str) -> bool:
        """发送文本消息"""
        context_token = self._context_tokens.get(to, "")
        if not context_token:
            return False

        try:
            self.api.send_text(to, text, context_token)
            return True
        except Exception as e:
            print(f"[Weixin] 文本发送失败: {e}")
            return False

    def message_handler(self):
        while True:
            if cnm.msg_stack:
                msg = cnm.msg_stack.pop(0)
                if '$$$' in msg:
                    msg = msg.split('$$$')
                    content = msg[0]
                    sys_cmd = msg[1].split(' ',maxsplit=2)
                    if sys_cmd[0] == 'timer':
                        self.send_text(self.from_user, content)
                        self.timer_mission(sys_cmd[1],sys_cmd[2])
                        self.send_text(self.from_user, f"[D] 已创建事件触发器，将于{int(sys_cmd[1])-round(time.time())}s后触发")
                    elif sys_cmd[0] == 'send':
                        sender.send(self.from_user,'',self.token,sys_cmd[1])
                    elif sys_cmd[0] == 'response':
                        if sys_cmd[1] == 'True':
                            self.xunsi = True
                        else:
                            self.xunsi = False
                else:
                    self.send_text(self.from_user, msg)
            time.sleep(0.5)

    def _process_message(self, raw_msg: dict):
        """处理单条消息"""
        msg_type = raw_msg.get('item_list', [{}])[0].get('type')
        if msg_type == 1:
            msg_id = str(raw_msg.get("message_id", raw_msg.get("seq", "")))
            if self._received_msgs.get(msg_id):
                return
            self._received_msgs[msg_id] = True

            from_user = raw_msg.get("from_user_id", "")
            context_token = raw_msg.get("context_token", "")

            self.from_user = from_user

            if context_token and from_user:
                self._context_tokens[from_user] = context_token

            item_list = raw_msg.get("item_list", [])
            text_content = ""

            for item in item_list:
                itype = item.get("type", 0)
                if itype == 1:
                    text_item = item.get("text_item", {})
                    text_content = text_item.get("text", "")
            if text_content:
                print(f"\n[Weixin] from={from_user} content={text_content}")
                if text_content.strip() == '#restart':
                    self._restart_reply_thread()
                else:
                    with self.msg_queue_lock:
                        self.msg_queue.append(text_content)
        elif msg_type == 2:
            full_url = raw_msg['item_list'][0]['image_item']['media']['full_url']
            encrypt_query_param = raw_msg['item_list'][0]['image_item']['media']['encrypt_query_param']
            aes_key = raw_msg['item_list'][0]['image_item']['media']['aes_key']
            file_path = f'{round(time.time())}.jpg'
            downloader.download(full_url, encrypt_query_param, aes_key, file_path)
            self.send_text(self.from_user, f'[D] 已保存图像')
        elif msg_type == 3:
            msg_id = str(raw_msg.get("message_id", raw_msg.get("seq", "")))
            if self._received_msgs.get(msg_id):
                return
            self._received_msgs[msg_id] = True
            from_user = raw_msg.get("from_user_id", "")
            context_token = raw_msg.get('item_list', [{}])[0].get('voice_item', {}).get('text')
            self.from_user = from_user
            if context_token and from_user:
                self._context_tokens[from_user] = context_token
            if context_token:
                print(f"\n[Weixin] from={from_user} content={context_token}")
                with self.msg_queue_lock:
                    self.msg_queue.append(context_token)
        elif msg_type == 4:
            full_url = raw_msg['item_list'][0]['file_item']['media']['full_url']
            encrypt_query_param = raw_msg['item_list'][0]['file_item']['media']['encrypt_query_param']
            aes_key = raw_msg['item_list'][0]['file_item']['media']['aes_key']
            file_path = raw_msg.get('item_list', [{}])[0].get('file_item', {}).get('file_name')
            downloader.download(full_url, encrypt_query_param, aes_key, file_path)
            self.send_text(self.from_user, f'[D] 已保存文件')
        elif msg_type == 5:
            full_url = raw_msg['item_list'][0]['video_item']['media']['full_url']
            encrypt_query_param = raw_msg['item_list'][0]['video_item']['media']['encrypt_query_param']
            aes_key = raw_msg['item_list'][0]['video_item']['media']['aes_key']
            file_path = f'{round(time.time())}.mp4'
            downloader.download(full_url, encrypt_query_param, aes_key, file_path)
            self.send_text(self.from_user, f'[D] 已保存视频')
        else:
            print(f"[Weixin] 收到未知类型消息: {msg_type}")

    def _restart_reply_thread(self):
        """终止当前的回复线程并重新启动"""
        print("[Weixin] 收到 #restart 指令，正在重启回复线程...")
        self._stop_event.set()
        
        if self.reply_thread and self.reply_thread.is_alive():
            self.reply_thread.join(timeout=3)
            if self.reply_thread.is_alive():
                print("[Weixin] 旧回复线程未能在规定时间内结束，已被强制忽略")
        
        with self.msg_queue_lock:
            self.msg_queue.clear()
            
        self._stop_event.clear()
        
        self.reply_thread = threading.Thread(target=self._reply_loop, daemon=True)
        self.reply_thread.start()
        
        self.send_text(self.from_user, "[D] 回复线程已重启")

    def _reply_loop(self):
        """回复线程循环"""        
        while not self._stop_event.is_set():
            try:
                with self.msg_queue_lock:
                    if self.msg_queue:
                        msg = self.msg_queue.pop(0)
                        if msg[0] != '#' and self.xunsi:
                            self.send_text(self.from_user, "[D] Agent开始寻思。")
                        
                        def _run_cnm(m):
                            cnm.CNMD(m)
                            
                        cnm_thread = threading.Thread(target=_run_cnm, args=(msg,))
                        cnm_thread.start()
                        
                        while cnm_thread.is_alive():
                            if self._stop_event.is_set():
                                print("[Weixin] 检测到重启指令，终止当前回复进程")
                                return 
                            cnm_thread.join(timeout=0.1)
                    else:
                        pass
                self._stop_event.wait(0.1)
                
            except Exception as e:
                print(f"[Weixin] 回复线程异常: {e}")
                self._stop_event.wait(1)

    def _poll_loop(self):
        """主长轮询循环"""
        print("[Weixin] 启动长轮询循环")
        while not self._stop_event.is_set():
            try:
                resp = self.api.get_updates(self._get_updates_buf)
                ret = resp.get("ret", 0)
                errcode = resp.get("errcode", 0)
                is_error = (ret != 0) or (errcode != 0)
                if is_error:
                    errmsg = resp.get("errmsg", "")
                    print(f"[Weixin] getUpdates错误: ret={ret} errcode={errcode} errmsg={errmsg}")
                    self._stop_event.wait(2)
                    continue

                new_buf = resp.get("get_updates_buf", "")
                if new_buf:
                    self._get_updates_buf = new_buf

                msgs = resp.get("msgs", [])
                for raw_msg in msgs:
                    try:
                        self._process_message(raw_msg)
                    except Exception as e:
                        print(f"[Weixin] 消息处理失败: {e}")

            except Exception as e:
                if self._stop_event.is_set():
                    break
                print(f"[Weixin] getUpdates异常: {e}")
                self._stop_event.wait(2)

        print("[Weixin] 长轮询循环结束")

    def start(self):
        """启动客户端"""
        if not self.login():
            print("[Weixin] 登录失败")
            return False

        self._stop_event.clear()
        
        self.reply_thread = threading.Thread(target=self._reply_loop, daemon=True)
        self.reply_thread.start()
        
        self._poll_loop()
        return True

    def stop(self):
        """停止客户端"""
        print("[Weixin] stop() called")
        self._stop_event.set()
        
        if self.reply_thread and self.reply_thread.is_alive():
            self.reply_thread.join(timeout=2)

    def timer_mission(self, timer, quest):
        print(f"[Weixin] 计时器开始 {round(time.time())} -> {timer}")
        def _run():
            nonlocal timer
            try:
                timer = float(timer)
                while True:
                    current_time = time.time()
                    if current_time >= timer:
                        print(f"[Weixin] 计时器触发")
                        self.msg_queue.append(quest)
                        break
                    time.sleep(0.1)
            except:
                return
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

def main():
    client = WeixinClient()

    msg_thread = threading.Thread(target=client.message_handler, daemon=True)
    msg_thread.start()
    try:
        if not client.start():
            print("[Weixin] 启动失败")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n[Weixin] 收到中断信号，正在停止...")
    finally:
        client.stop()

    print("[Weixin] 程序已退出")


if __name__ == "__main__":
    main()

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import uuid
from datetime import datetime
import threading
import time
import CNMD

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# 存储在线用户
online_users = {}

# 创建 CNMD 实例
cnm = CNMD.CNMD()

# 存储接收到的消息队列
msg_queue = []

# 线程锁
queue_lock = threading.Lock()

# 命令开始处理的时间
cmd_start_time = None

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    client_id = str(uuid.uuid4())[:8]
    online_users[request.sid] = {
        'id': client_id,
        'sid': request.sid,
        'device_type': request.args.get('device_type', 'desktop'),
        'connected_at': datetime.now().isoformat()
    }

    emit('connected', {
        'client_id': client_id,
        'message': '连接成功'
    })

    # 广播用户列表更新
    broadcast_user_list()

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接"""
    if request.sid in online_users:
        user = online_users[request.sid]
        del online_users[request.sid]
        emit('user_left', {
            'user_id': user['id'],
            'message': f'用户 {user["id"]} 已离开'
        }, broadcast=True)
        broadcast_user_list()

@socketio.on('send_message')
def handle_send_message(data):
    """处理发送消息"""
    message = data.get('message', '')

    if not message:
        return

    with queue_lock:
        msg_queue.append(message)

    user = online_users.get(request.sid, {})
    message_data = {
        'id': str(uuid.uuid4())[:8],
        'user_id': user.get('id', 'unknown'),
        'device_type': user.get('device_type', 'unknown'),
        'content': message[:1000],  # 限制消息长度
        'timestamp': datetime.now().isoformat()
    }

    emit('new_message', message_data, broadcast=True)

@socketio.on('get_users')
def handle_get_users():
    """获取在线用户列表"""
    users_list = list(online_users.values())
    emit('users_list', {'users': users_list})

def broadcast_user_list():
    """广播更新后的用户列表"""
    users_list = list(online_users.values())
    socketio.emit('users_list', {'users': users_list})

def msg_sender():
    """发送线程：当msg_stack非空时发送并弹出第一条"""
    while True:
        if cnm.msg_stack:
            with queue_lock:
                msg = cnm.msg_stack.pop(0)
            socketio.emit('new_message', {
                'id': str(uuid.uuid4())[:8],
                'user_id': 'system',
                'device_type': 'system',
                'content': msg,
                'timestamp': datetime.now().isoformat()
            })
        time.sleep(0.5)

def msg_processor():
    """处理线程：从队列取出消息并传入CNMD处理"""
    while True:
        with queue_lock:
            if msg_queue:
                cmd = msg_queue.pop(0)
                cnm.CNMD(cmd)
                # 记录命令开始处理的时间
                cmd_start_time = time.time()

        # 检查是否有命令正在处理且超过3分钟
        if 'cmd_start_time' in locals() and (time.time() - cmd_start_time > 180):
            # 强制停止CNMD
            try:
                cnm.stop()  # 假设CNMD有stop方法
            except:
                pass
            # 在消息队列中加入超时信息
            with queue_lock:
                cnm.msg_stack.append("命令执行超时，已强制停止")
            # 清除开始时间标记
            del cmd_start_time

        time.sleep(0.5)

if __name__ == '__main__':
    print("局域网通讯系统已启动")
    print("访问地址: http://localhost:5000")

    # 启动消息发送线程
    sender_thread = threading.Thread(target=msg_sender, daemon=True)
    sender_thread.start()

    # 启动消息处理线程
    processor_thread = threading.Thread(target=msg_processor, daemon=True)
    processor_thread.start()

    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

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

online_users = {}

cnm = CNMD.CNMD()
msg_queue = []

queue_lock = threading.Lock()

cmd_start_time = None

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    try:
        client_id = str(uuid.uuid4())[:8]
        device_type = request.args.get('device_type', 'desktop')
        
        online_users[request.sid] = {
            'id': client_id,
            'sid': request.sid,
            'device_type': device_type,
            'connected_at': datetime.now().isoformat(),
            'custom_id': client_id,
            'bubble_color': '#e3f2fd'
        }

        print(f"用户 {client_id} 已连接 (设备类型: {device_type})")
        
        emit('connected', {
            'client_id': client_id,
            'custom_id': client_id,
            'message': f'连接成功！您的ID是: {client_id}'
        }, room=request.sid)

        broadcast_user_list()
        
    except Exception as e:
        print(f"连接处理错误: {e}")
        emit('error', {'message': '连接处理失败'}, room=request.sid)

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

    stripped_msg = message.strip()
    if stripped_msg.startswith("@bot") or stripped_msg.startswith("#"):
        with queue_lock:
            if stripped_msg.startswith("@bot"):
                processed_msg = stripped_msg[4:].strip()
            else:
                processed_msg = stripped_msg            
            msg_queue.append(processed_msg)


    user = online_users.get(request.sid, {})
    message_data = {
        'id': str(uuid.uuid4())[:8],
        'user_id': user.get('id', 'unknown'),
        'custom_id': user.get('custom_id', user.get('id', 'unknown')),
        'device_type': user.get('device_type', 'unknown'),
        'bubble_color': user.get('bubble_color', '#e3f2fd'),
        'content': message[:1000],
        'timestamp': datetime.now().isoformat()
    }

    emit('new_message', message_data, broadcast=True)

@socketio.on('get_users')
def handle_get_users():
    """获取在线用户列表"""
    users_list = list(online_users.values())
    emit('users_list', {'users': users_list})

@socketio.on('update_custom_id')
def handle_update_custom_id(data):
    """更新用户自定义ID"""
    try:
        custom_id = data.get('custom_id', '').strip()
        
        if not custom_id:
            emit('custom_id_updated', {
                'success': False,
                'message': '自定义ID不能为空'
            }, room=request.sid)
            return
            
        if len(custom_id) > 20:
            emit('custom_id_updated', {
                'success': False,
                'message': '自定义ID长度不能超过20个字符'
            }, room=request.sid)
            return
            
        import re
        if re.search(r'[^\w\s\u4e00-\u9fa5]', custom_id):
            emit('custom_id_updated', {
                'success': False,
                'message': '自定义ID只能包含中文、英文、数字和下划线'
            }, room=request.sid)
            return
            
        if request.sid in online_users:
            old_id = online_users[request.sid].get('custom_id', online_users[request.sid]['id'])
            online_users[request.sid]['custom_id'] = custom_id
            
            print(f"用户 {online_users[request.sid]['id']} 更新自定义ID: {old_id} -> {custom_id}")
            
            emit('custom_id_updated', {
                'success': True,
                'message': f'自定义ID已更新为: {custom_id}',
                'custom_id': custom_id
            }, room=request.sid)
            broadcast_user_list()
        else:
            emit('custom_id_updated', {
                'success': False,
                'message': '用户未连接'
            }, room=request.sid)
            
    except Exception as e:
        print(f"自定义ID更新错误: {e}")
        emit('custom_id_updated', {
            'success': False,
            'message': '更新失败，请稍后重试'
        }, room=request.sid)

@socketio.on('update_bubble_color')
def handle_update_bubble_color(data):
    """更新用户气泡颜色"""
    try:
        bubble_color = data.get('bubble_color', '').strip()
        if bubble_color and len(bubble_color) <= 7:
            if request.sid in online_users:
                online_users[request.sid]['bubble_color'] = bubble_color
                emit('bubble_color_updated', {
                    'success': True,
                    'message': '气泡颜色更新成功',
                    'bubble_color': bubble_color
                }, room=request.sid)
                broadcast_user_list()
            else:
                emit('bubble_color_updated', {
                    'success': False,
                    'message': '用户未连接'
                }, room=request.sid)
        else:
            emit('bubble_color_updated', {
                'success': False,
                'message': '颜色格式无效'
            }, room=request.sid)
    except Exception as e:
        print(f"气泡颜色更新错误: {e}")
        emit('bubble_color_updated', {
            'success': False,
            'message': '更新失败，请稍后重试'
        }, room=request.sid)

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
    global cmd_start_time
    while True:
        with queue_lock:
            if msg_queue:
                cmd = msg_queue.pop(0)
                cnm.CNMD(cmd)
                cmd_start_time = time.time()

        if cmd_start_time is not None and (time.time() - cmd_start_time > 180):
            with queue_lock:
                #cnm.msg_stack.append("警告：命令执行超时")
                print('警告：命令执行超时')
            cmd_start_time = None

        time.sleep(0.5)

if __name__ == '__main__':
    print("局域网通讯系统已启动")
    print("访问地址: http://localhost:5000")

    sender_thread = threading.Thread(target=msg_sender, daemon=True)
    sender_thread.start()

    processor_thread = threading.Thread(target=msg_processor, daemon=True)
    processor_thread.start()

    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

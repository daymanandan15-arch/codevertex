from flask import request
from flask_socketio import emit
from app.extensions import socketio

# Track online users for simple presence (sid -> username)
online_users = {}

@socketio.on('connect')
def handle_connect():
    # We can emit connection info here
    pass

@socketio.on('join')
def handle_join(data):
    username = data.get('username', 'Anonymous')
    online_users[request.sid] = username
    # Inform all connected clients that a user joined
    emit('system_message', {'msg': f'{username} joined the global chat.'}, broadcast=True)
    # Send history or current user count if desired, but we'll stick to simple live chat
    emit('system_message', {'msg': 'Welcome to CoreStack Global Chat!'}, to=request.sid)

@socketio.on('chat_message')
def handle_message(data):
    username = data.get('username', 'Anonymous')
    msg = data.get('msg', '').strip()
    if msg:
        emit('chat_message', {'username': username, 'msg': msg}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    username = online_users.get(request.sid)
    if username:
        del online_users[request.sid]
        emit('system_message', {'msg': f'{username} left.'}, broadcast=True)

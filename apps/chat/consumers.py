"""
Chat WebSocket consumers for QA Chatbot System
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    채팅 WebSocket 컨슈머
    """
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        클라이언트로부터 메시지 수신
        """
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        message_type = text_data_json.get('type', 'user')

        # 여기서 LangGraph 오케스트레이터를 호출하여 메시지 처리
        # 실제 구현에서는 services.langgraph_service 를 사용
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'message_type': message_type,
                'session_id': self.session_id
            }
        )

    async def chat_message(self, event):
        """
        그룹으로부터 메시지 수신
        """
        message = event['message']
        message_type = event['message_type']
        session_id = event['session_id']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'type': message_type,
            'session_id': session_id
        })) 
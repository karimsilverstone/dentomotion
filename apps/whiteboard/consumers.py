"""
WebSocket consumers for real-time whiteboard functionality
This requires Django Channels to be properly configured
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.whiteboard.models import WhiteboardSession


class WhiteboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time whiteboard collaboration
    Handles drawing events, text, image uploads, and PDF display
    """
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'whiteboard_{self.session_id}'
        
        # Verify user is authenticated
        user = self.scope['user']
        
        # Debug logging
        print(f"[WEBSOCKET] Connection attempt for session {self.session_id}")
        print(f"[WEBSOCKET] User: {user}")
        print(f"[WEBSOCKET] Is authenticated: {user.is_authenticated}")
        
        if not user.is_authenticated:
            print(f"[WEBSOCKET] ❌ User not authenticated - closing connection")
            await self.close(code=1008)
            return
        
        # Verify session exists and is active
        session = await self.get_session(self.session_id)
        if not session:
            print(f"[WEBSOCKET] ❌ Session {self.session_id} not found")
            await self.close(code=3000)
            return
        
        if not session.is_active:
            print(f"[WEBSOCKET] ❌ Session {self.session_id} is not active")
            await self.close(code=3001)
            return
        
        print(f"[WEBSOCKET] ✅ Session {self.session_id} is valid and active")
        
        # Verify user has access to this session
        has_access = await self.verify_access(user, session)
        if not has_access:
            print(f"[WEBSOCKET] ❌ User {user.id} does not have access to session {self.session_id}")
            await self.close(code=3002)
            return
        
        print(f"[WEBSOCKET] ✅ User {user.id} ({user.role}) has access to session")
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        print(f"[WEBSOCKET] ✅ User {user.id} joined room {self.room_group_name}")
        
        await self.accept()
        
        print(f"[WEBSOCKET] ✅ WebSocket connection accepted for user {user.id}")
        
        # Send join notification to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': user.id,
                'user_name': user.get_full_name(),
                'user_role': user.role
            }
        )
        
        print(f"[WEBSOCKET] ✅ Sent user_joined notification for {user.get_full_name()}")
    
    async def disconnect(self, close_code):
        user = self.scope['user']
        
        # Send leave notification to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': user.id,
                'user_name': user.get_full_name()
            }
        )
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        data = json.loads(text_data)
        action_type = data.get('type')
        
        user = self.scope['user']
        
        # Add user info to the message
        data['user_id'] = user.id
        data['user_name'] = user.get_full_name()
        data['timestamp'] = data.get('timestamp')
        
        # Broadcast to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'whiteboard_message',
                'message': data
            }
        )
    
    async def whiteboard_message(self, event):
        """Send whiteboard message to WebSocket"""
        message = event['message']
        await self.send(text_data=json.dumps(message))
    
    async def user_joined(self, event):
        """Send user joined notification"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'user_role': event['user_role']
        }))
    
    async def user_left(self, event):
        """Send user left notification"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'user_name': event['user_name']
        }))
    
    @database_sync_to_async
    def get_session(self, session_id):
        """Get whiteboard session from database"""
        try:
            return WhiteboardSession.objects.select_related('class_instance', 'teacher').get(id=session_id)
        except WhiteboardSession.DoesNotExist:
            return None
    
    @database_sync_to_async
    def verify_access(self, user, session):
        """Verify user has access to the whiteboard session"""
        from apps.classes.models import TeacherAssignment, Enrolment
        
        # Teachers must be assigned to the class
        if user.role == 'TEACHER':
            return TeacherAssignment.objects.filter(
                teacher=user,
                class_instance=session.class_instance
            ).exists()
        
        # Students must be enrolled in the class
        if user.role == 'STUDENT':
            return Enrolment.objects.filter(
                student=user,
                class_instance=session.class_instance,
                is_active=True
            ).exists()
        
        # Managers and admins have access
        if user.role in ['CENTRE_MANAGER', 'SUPER_ADMIN']:
            return True
        
        return False


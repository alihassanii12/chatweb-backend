import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()


class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'room_{self.room_id}'

        # Extract token from query parameters
        query_string = self.scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        # Authenticate user from JWT token passed securely during handshake
        self.user = await self.get_user_from_jwt(token)
        
        if self.user.is_anonymous:
            # Reject connection if unauthorized
            await self.close(code=4001)
            return

        if not await self.user_has_room_access():
            await self.close(code=4003)
            return

        # Join the unique private room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        # Broadcast notification that partner joined the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'room_notification',
                'action': 'join',
                'username': self.user.username,
                'email': self.user.email
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'user') and not self.user.is_anonymous:
            # Broadcast notification that partner left the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'room_notification',
                    'action': 'leave',
                    'username': self.user.username,
                    'email': self.user.email
                }
            )
            # Remove connection channel from the group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Receive payload structures from WebSocket client
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except Exception:
            return

        msg_type = data.get('type')

        if msg_type == 'chat':
            message_content = data.get('message', '')
            if message_content.strip():
                # Save the persistent message record inside PostgreSQL database
                await self.save_chat_message(self.user, message_content)
                # Broadcast the message to the partner
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message_content,
                        'sender_id': self.user.id,
                        'sender_name': self.user.username,
                        'sender_email': self.user.email
                    }
                )

        elif msg_type == 'video_sync':
            action = data.get('action')  # 'play', 'pause', 'seek', 'change_video'
            current_time = data.get('currentTime', 0.0)
            video_url = data.get('videoUrl', None)
            
            # Save the synced playback state parameters in PostgreSQL
            await self.update_room_sync_state(action, current_time, video_url)
            
            # Broadcast playback synchronization instruction to the other browser tab
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'video_sync_message',
                    'sender_channel': self.channel_name,
                    'action': action,
                    'currentTime': current_time,
                    'videoUrl': video_url,
                    'username': self.user.username
                }
            )

        elif msg_type == 'webrtc':
            payload = data.get('payload')
            # Forward peer connection details (SDP description or ICE Candidate) to the other tab
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_message',
                    'sender_channel': self.channel_name,
                    'payload': payload
                }
            )

        elif msg_type == 'typing':
            is_typing = data.get('is_typing', False)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_message',
                    'sender_channel': self.channel_name,
                    'is_typing': is_typing,
                    'username': self.user.username
                }
            )

    # Handlers for Group broadcast events
    async def room_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'action': event['action'],
            'username': event['username'],
            'email': event['email']
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'sender_email': event['sender_email']
        }))

    async def video_sync_message(self, event):
        # Exclude the sender to prevent infinite trigger reflection
        if self.channel_name != event['sender_channel']:
            await self.send(text_data=json.dumps({
                'type': 'video_sync',
                'action': event['action'],
                'currentTime': event['currentTime'],
                'videoUrl': event['videoUrl'],
                'username': event['username']
            }))

    async def webrtc_message(self, event):
        # Only forward signal connection packages to the remote peer
        if self.channel_name != event['sender_channel']:
            await self.send(text_data=json.dumps({
                'type': 'webrtc',
                'payload': event['payload']
            }))

    async def typing_message(self, event):
        if self.channel_name != event['sender_channel']:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'is_typing': event['is_typing'],
                'username': event['username']
            }))

    # Helper async database operations
    @database_sync_to_async
    def user_has_room_access(self):
        from .models import Room
        from .permissions import GLOBAL_ROOM_ID, user_can_access_room

        try:
            room = Room.objects.get(id=self.room_id)
        except Room.DoesNotExist:
            return self.room_id == GLOBAL_ROOM_ID

        return user_can_access_room(room, self.user)

    @database_sync_to_async
    def get_user_from_jwt(self, token):
        if not token:
            return AnonymousUser()
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except Exception:
            return AnonymousUser()

    @database_sync_to_async
    def save_chat_message(self, user, content):
        from .models import Room, ChatMessage
        try:
            room = Room.objects.get(id=self.room_id)
            ChatMessage.objects.create(room=room, sender=user, content=content)
        except Exception as e:
            print(f"Error saving chat message to db: {e}")

    @database_sync_to_async
    def update_room_sync_state(self, action, current_time, video_url):
        from .models import Room, RoomMedia
        try:
            room = Room.objects.get(id=self.room_id)
            if action == 'play':
                room.is_playing = True
                room.current_time = current_time
            elif action == 'pause':
                room.is_playing = False
                room.current_time = current_time
            elif action == 'seek':
                room.current_time = current_time
            elif action == 'change_video':
                if video_url:
                    room.current_video_url = video_url
                    room.current_time = 0.0
                    room.is_playing = False

                    parsed_title = video_url.split('/')[-1]
                    if not parsed_title or 'youtube.com' in video_url or 'youtu.be' in video_url:
                        parsed_title = 'YouTube Shared Video'
                    else:
                        parsed_title = parsed_title.split('?')[0]

                    RoomMedia.objects.create(
                        room=room,
                        added_by=self.user,
                        video_url=video_url,
                        title=parsed_title[:250],
                    )
                else:
                    room.current_video_url = None
                    room.current_time = 0.0
                    room.is_playing = False
            room.save()
        except Exception as e:
            print(f"Error updating database room sync: {e}")

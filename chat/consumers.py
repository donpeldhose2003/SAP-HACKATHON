import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from ai_engine import chatbot
from attendees.models import AttendeeProfile
from chat.models import UserActivity

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_authenticated:
            # Join user-specific group for personalized updates
            self.user_group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            
            # Log connection activity
            await self.log_activity("chat_connected", {"timestamp": str(timezone.now())})
        
        await self.accept()
        
        # Send welcome message if user is authenticated
        if self.user.is_authenticated:
            welcome_response = await self.get_welcome_message()
            await self.send(text_data=json.dumps({
                'type': 'welcome',
                'message': welcome_response,
                'live_feed': await self.get_live_feed()
            }))

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            # Leave user group
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            
            # Log disconnection
            await self.log_activity("chat_disconnected", {"close_code": close_code})

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_chat_message(text_data_json)
            elif message_type == 'get_feed':
                await self.handle_feed_request()
            elif message_type == 'action':
                await self.handle_action(text_data_json)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message format'
            }))

    async def handle_chat_message(self, data):
        message = data.get('message', '')
        
        if not message.strip():
            return
        
        # Log user message activity
        await self.log_activity("user_message", {"message": message})
        
        # Get AI response
        ai_response = await self.get_ai_response(message)
        
        # Get updated live feed
        live_feed = await self.get_live_feed()
        
        # Send response back to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'bot_response',
            'message': ai_response,
            'live_feed': live_feed,
            'timestamp': str(timezone.now())
        }))

    async def handle_feed_request(self):
        """Handle request for updated live feed"""
        live_feed = await self.get_live_feed()
        await self.send(text_data=json.dumps({
            'type': 'feed_update',
            'live_feed': live_feed
        }))

    async def handle_action(self, data):
        """Handle user actions from the feed"""
        action = data.get('action', '')
        item_type = data.get('item_type', '')
        
        # Log the action
        await self.log_activity("feed_action", {
            "action": action,
            "item_type": item_type
        })
        
        # Process action as a chat message
        await self.handle_chat_message({'message': action})

    @database_sync_to_async
    def get_ai_response(self, message):
        """Get response from AI chatbot"""
        return chatbot.get_response(message, user_context=self.user)

    @database_sync_to_async
    def get_welcome_message(self):
        """Get welcome message for new connections"""
        if not self.user.is_authenticated:
            return chatbot.get_response("", user_context=None)
        
        # Return empty string to trigger welcome in chatbot logic
        return chatbot.get_response("", user_context=self.user)

    @database_sync_to_async
    def get_live_feed(self):
        """Get personalized live feed"""
        return chatbot.get_live_feed(self.user)

    @database_sync_to_async
    def log_activity(self, activity_type, activity_data):
        """Log user activity"""
        if self.user.is_authenticated:
            UserActivity.objects.create(
                user=self.user,
                activity_type=activity_type,
                activity_data=activity_data
            )

    # Handle messages sent to user group
    async def user_notification(self, event):
        """Handle notifications sent to user group"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message'],
            'notification_type': event.get('notification_type', 'info')
        }))
    
    async def feed_update(self, event):
        """Handle live feed updates"""
        await self.send(text_data=json.dumps({
            'type': 'feed_update',
            'live_feed': event['live_feed']
        }))
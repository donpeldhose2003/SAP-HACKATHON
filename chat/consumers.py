import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.core.cache import cache
from ai_engine import chatbot
from attendees.models import AttendeeProfile
from chat.models import UserActivity
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.user_group_name = None
        self.is_typing = False
        self.last_activity = timezone.now()
        self.isConnected = False
        
        try:
            if self.user.is_authenticated:
                # Join user-specific group for personalized updates
                self.user_group_name = f"user_{self.user.id}"
                await self.channel_layer.group_add(
                    self.user_group_name,
                    self.channel_name
                )
                
                # Log connection activity
                await self.log_activity("chat_connected", {
                    "timestamp": str(timezone.now()),
                    "connection_info": "websocket_connected"
                })
                
                # Set user as online
                await self.set_user_status("online")
            
            await self.accept()
            self.isConnected = True
            
            # Send welcome message if user is authenticated
            if self.user.is_authenticated:
                try:
                    logger.info(f"Getting welcome message for user {self.user.username}")
                    welcome_response = await self.get_welcome_message()
                    logger.info(f"Getting live feed for user {self.user.username}")
                    live_feed = await self.get_live_feed()
                    logger.info(f"Getting user info for user {self.user.username}")
                    user_info = await self.get_user_info()
                    
                    logger.info(f"Sending welcome message to user {self.user.username}")
                    await self.send(text_data=json.dumps({
                        'type': 'welcome',
                        'message': welcome_response,
                        'live_feed': live_feed,
                        'user_info': user_info
                    }))
                    
                    logger.info(f"Welcome message sent successfully to user {self.user.username}")
                    # Start periodic feed updates after a delay
                    asyncio.create_task(self.start_periodic_updates_delayed())
                except Exception as e:
                    logger.error(f"Error sending welcome message to user {self.user.username}: {e}")
                    await self.send(text_data=json.dumps({
                        'type': 'welcome',
                        'message': "Welcome to AURA! I'm ready to help you.",
                        'live_feed': [
                            {
                                'title': '🎉 Welcome to AURA!',
                                'content': 'Your personalized event feed will appear here. Chat with me to get started!',
                                'action': 'Get Started',
                                'type': 'welcome',
                                'priority': 'high'
                            }
                        ],
                        'user_info': {'username': self.user.username}
                    }))
            else:
                logger.warning("Unauthenticated user attempted WebSocket connection")
                
        except Exception as e:
            logger.error(f"Error in WebSocket connect: {e}")
            await self.close()

    async def disconnect(self, close_code):
        self.isConnected = False
        if self.user.is_authenticated:
            # Leave user group
            if self.user_group_name:
                await self.channel_layer.group_discard(
                    self.user_group_name,
                    self.channel_name
                )
            
            # Set user as offline
            await self.set_user_status("offline")
            
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

    @database_sync_to_async
    def set_user_status(self, status):
        """Set user online/offline status"""
        if self.user.is_authenticated:
            cache_key = f"user_status_{self.user.id}"
            cache.set(cache_key, status, 300)  # 5 minutes

    @database_sync_to_async
    def get_user_info(self):
        """Get user information for the client"""
        if self.user.is_authenticated:
            try:
                profile = AttendeeProfile.objects.get(user=self.user)
                return {
                    "username": self.user.username,
                    "first_name": self.user.first_name,
                    "company": profile.company,
                    "interests": profile.interests
                }
            except AttendeeProfile.DoesNotExist:
                return {
                    "username": self.user.username,
                    "first_name": self.user.first_name
                }
        return {}

    async def start_periodic_updates_delayed(self):
        """Start periodic updates after initial connection is stable"""
        try:
            # Wait 5 seconds before starting periodic updates
            await asyncio.sleep(5)
            if self.isConnected and self.user.is_authenticated:
                logger.info(f"Starting periodic updates for user {self.user.username}")
                await self.periodic_feed_updates()
        except Exception as e:
            logger.error(f"Error starting delayed periodic updates: {e}")

    async def periodic_feed_updates(self):
        """Send periodic feed updates"""
        try:
            while self.isConnected:
                await asyncio.sleep(60)  # Update every minute
                if self.user.is_authenticated and self.isConnected:
                    live_feed = await self.get_live_feed()
                    await self.send(text_data=json.dumps({
                        'type': 'feed_update',
                        'live_feed': live_feed
                    }))
        except Exception as e:
            logger.error(f"Error in periodic updates: {e}")
            # Don't let periodic update errors close the connection

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
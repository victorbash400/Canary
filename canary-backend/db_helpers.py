# db_helpers.py - Database helper functions

import boto3
import os
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# Table references
users_table = dynamodb.Table(os.environ['USERS_TABLE'])
chats_table = dynamodb.Table(os.environ['CHATS_TABLE'])
messages_table = dynamodb.Table(os.environ['MESSAGES_TABLE'])
user_memory_table = dynamodb.Table(os.environ['USER_MEMORY_TABLE'])

class DatabaseHelpers:
    
    # USER OPERATIONS
    @staticmethod
    def create_user(email, password_hash, username=None):
        """Create a new user"""
        user_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat() + "Z"
        
        user_data = {
            'userId': user_id,
            'email': email,
            'passwordHash': password_hash,
            'username': username or email.split('@')[0],
            'createdAt': timestamp,
            'lastActive': timestamp,
            'preferences': {
                'interests': [],
                'monitoring_topics': [],
                'relevance_threshold': 75,
                'update_frequency': 'hourly',
                'urgent_alerts': True,
                'email_notifications': False,
                'email_frequency_hours': 1  # Default to hourly notifications
            }
        }
        
        users_table.put_item(Item=user_data)
        return user_data
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        try:
            response = users_table.query(
                IndexName='EmailIndex',
                KeyConditionExpression=Key('email').eq(email)
            )
            return response['Items'][0] if response['Items'] else None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        try:
            response = users_table.get_item(Key={'userId': user_id})
            return response.get('Item')
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    @staticmethod
    def update_user_preferences(user_id, preferences):
        """Update user preferences"""
        try:
            users_table.update_item(
                Key={'userId': user_id},
                UpdateExpression='SET preferences = :prefs, lastActive = :timestamp',
                ExpressionAttributeValues={
                    ':prefs': preferences,
                    ':timestamp': datetime.now().isoformat() + "Z"
                }
            )
            return True
        except Exception as e:
            print(f"Error updating preferences: {e}")
            return False
    
    # CHAT OPERATIONS
    @staticmethod
    def create_chat(user_id, title="New Chat"):
        """Create a new chat"""
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat() + "Z"
        
        chat_data = {
            'chatId': chat_id,
            'userId': user_id,
            'title': title,
            'createdAt': timestamp,
            'lastMessageAt': timestamp,
            'messageCount': 0,
            'isActive': True
        }
        
        chats_table.put_item(Item=chat_data)
        return chat_data
    
    @staticmethod
    def get_user_chats(user_id):
        """Get all chats for a user"""
        try:
            response = chats_table.query(
                IndexName='UserChatsIndex',
                KeyConditionExpression=Key('userId').eq(user_id),
                ScanIndexForward=False  # Most recent first
            )
            return response['Items']
        except Exception as e:
            print(f"Error getting user chats: {e}")
            return []
    
    @staticmethod
    def get_chat(chat_id):
        """Get specific chat"""
        try:
            response = chats_table.get_item(Key={'chatId': chat_id})
            return response.get('Item')
        except Exception as e:
            print(f"Error getting chat: {e}")
            return None
    
    @staticmethod
    def update_chat_activity(chat_id):
        """Update chat's last message time"""
        try:
            chats_table.update_item(
                Key={'chatId': chat_id},
                UpdateExpression='SET lastMessageAt = :timestamp, messageCount = messageCount + :inc',
                ExpressionAttributeValues={
                    ':timestamp': datetime.now().isoformat() + "Z",
                    ':inc': 1
                }
            )
        except Exception as e:
            print(f"Error updating chat activity: {e}")
    
    # MESSAGE OPERATIONS
    @staticmethod
    def save_message(chat_id, user_id, content, role, message_type="text"):
        """Save a message"""
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat() + "Z"
        
        message_data = {
            'messageId': message_id,
            'chatId': chat_id,
            'userId': user_id,
            'content': content,
            'role': role,
            'timestamp': timestamp,
            'messageType': message_type
        }
        
        messages_table.put_item(Item=message_data)
        
        # Update chat activity
        DatabaseHelpers.update_chat_activity(chat_id)
        
        return message_data
    
    @staticmethod
    def get_chat_messages(chat_id, limit=100):
        """Get messages for a chat with better ordering and limit handling"""
        try:
            response = messages_table.query(
                IndexName='ChatMessagesIndex',
                KeyConditionExpression=Key('chatId').eq(chat_id),
                ScanIndexForward=True,  # Oldest first for conversation context
                Limit=limit
            )
            messages = response['Items']
            
            # Sort by timestamp to ensure proper order
            messages.sort(key=lambda x: x.get('timestamp', ''))
            
            return messages
        except Exception as e:
            print(f"Error getting chat messages: {e}")
            return []
    
    @staticmethod
    def get_recent_messages(chat_id, limit=10):
        """Get most recent messages for context (newest first)"""
        try:
            response = messages_table.query(
                IndexName='ChatMessagesIndex',
                KeyConditionExpression=Key('chatId').eq(chat_id),
                ScanIndexForward=False,  # Newest first
                Limit=limit
            )
            messages = response['Items']
            
            # Reverse to get chronological order for conversation context
            return list(reversed(messages))
        except Exception as e:
            print(f"Error getting recent messages: {e}")
            return []
    
    # USER MEMORY OPERATIONS
    @staticmethod
    def update_user_memory(user_id, memory_snapshot, extracted_interests):
        """Update AI-generated user memory"""
        try:
            # Get existing memory to increment conversation count
            existing_memory = DatabaseHelpers.get_user_memory(user_id)
            conversation_count = 1
            
            if existing_memory:
                conversation_count = existing_memory.get('conversationCount', 0) + 1
            
            user_memory_table.put_item(
                Item={
                    'userId': user_id,
                    'memorySnapshot': memory_snapshot,
                    'extractedInterests': extracted_interests,
                    'lastUpdated': datetime.now().isoformat() + "Z",
                    'conversationCount': conversation_count
                }
            )
            return True
        except Exception as e:
            print(f"Error updating user memory: {e}")
            return False
    
    @staticmethod
    def get_user_memory(user_id):
        """Get user memory"""
        try:
            response = user_memory_table.get_item(Key={'userId': user_id})
            return response.get('Item')
        except Exception as e:
            print(f"Error getting user memory: {e}")
            return None
    
    @staticmethod
    def append_to_user_memory(user_id, additional_context):
        """Append new context to existing memory without overwriting"""
        try:
            existing_memory = DatabaseHelpers.get_user_memory(user_id)
            
            if existing_memory:
                current_snapshot = existing_memory.get('memorySnapshot', '')
                updated_snapshot = f"{current_snapshot}\n\nRecent context: {additional_context}".strip()
                
                # Keep memory snapshot under reasonable length
                if len(updated_snapshot) > 2000:
                    # Keep only the most recent 1500 characters
                    updated_snapshot = "..." + updated_snapshot[-1500:]
                
                user_memory_table.update_item(
                    Key={'userId': user_id},
                    UpdateExpression='SET memorySnapshot = :snapshot, lastUpdated = :timestamp, conversationCount = conversationCount + :inc',
                    ExpressionAttributeValues={
                        ':snapshot': updated_snapshot,
                        ':timestamp': datetime.now().isoformat() + "Z",
                        ':inc': 1
                    }
                )
            else:
                # Create new memory if none exists
                DatabaseHelpers.update_user_memory(user_id, additional_context, [])
            
            return True
        except Exception as e:
            print(f"Error appending to user memory: {e}")
            return False
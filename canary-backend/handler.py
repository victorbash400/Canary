# handler.py - Main entry point that delegates to specific modules

import json
from utils import get_cors_headers
from auth_handlers import register_user, login_user, get_user_profile
from news_handlers import get_news_feed, get_user_preferences, update_user_preferences, add_monitoring_topic, remove_monitoring_topic, get_urgent_news
from chat_handlers import create_new_chat, get_all_chats, get_chat_by_id, save_message, get_ai_memory

def cors_handler(event, context):
    """Handle CORS preflight requests"""
    return {
        "statusCode": 200,
        "headers": get_cors_headers(),
        "body": json.dumps({"message": "CORS OK"})
    }

# Export all functions for Serverless
__all__ = [
    # Auth functions
    'register_user',
    'login_user', 
    'get_user_profile',
    
    # News functions
    'get_news_feed',
    'get_user_preferences',
    'update_user_preferences',
    'add_monitoring_topic',
    'remove_monitoring_topic',
    'get_urgent_news',
    
    # Chat functions
    'create_new_chat',
    'get_all_chats',
    'get_chat_by_id',
    'save_message',
    'get_ai_memory',
    
    # CORS handler
    'cors_handler'
]
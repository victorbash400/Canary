## chat_handlers.py - Chat related functions

import json
import requests
import os
import traceback
from datetime import datetime
from db_helpers import DatabaseHelpers
from utils import get_cors_headers, extract_user_from_token
from email_preference_handlers import (
    extract_email_preferences_from_conversation, 
    update_email_preferences_internal,
    send_email_preference_confirmation
)

def extract_preferences_from_conversation(conversation_text, user_id):
    """Extract preference changes from conversation using Gemini"""
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key:
        return {"add": [], "remove": []}
    
    prompt = f"""
    Analyze this conversation and extract any topics the user wants to ADD or REMOVE from their news monitoring.

    Conversation: {conversation_text}

    Look for phrases like:
    - "track Tesla", "follow Apple", "monitor crypto", "keep me updated on AI"
    - "stop tracking", "remove crypto", "don't want Bitcoin updates", "unfollow"
    - Company names, stock symbols, technologies, industries they mention wanting updates on

    Return ONLY a JSON object with this exact format:
    {{
        "add": ["topic1", "topic2"],
        "remove": ["topic3"],
        "reasoning": "brief explanation of what you detected"
    }}

    Be specific with topic names. For example:
    - "Tesla stock" not just "Tesla"
    - "AI developments" not just "AI"
    - "Python jobs" not just "Python"
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            
            if data and 'candidates' in data and len(data['candidates']) > 0:
                candidate = data['candidates'][0]
                
                if 'content' in candidate and 'parts' in candidate['content']:
                    gemini_text = candidate['content']['parts'][0]['text']
                    gemini_text = gemini_text.replace('```json', '').replace('```', '').strip()
                    
                    try:
                        preference_changes = json.loads(gemini_text)
                        return preference_changes
                    except Exception:
                        return {"add": [], "remove": []}
                else:
                    return {"add": [], "remove": []}
            else:
                return {"add": [], "remove": []}
        else:
            return {"add": [], "remove": []}
                
    except Exception:
        return {"add": [], "remove": []}

def add_monitoring_topic_internal(user_id, topic):
    """Internal function to add monitoring topic without HTTP wrapper"""
    try:
        user = DatabaseHelpers.get_user_by_id(user_id)
        
        if not user:
            return False
        
        current_prefs = user.get('preferences', {})
        monitoring_topics = current_prefs.get('monitoring_topics', [])
        
        if topic and topic not in monitoring_topics:
            monitoring_topics.append(topic)
            current_prefs['monitoring_topics'] = monitoring_topics
            
            DatabaseHelpers.update_user_preferences(user_id, current_prefs)
            return True
        
        return False
        
    except Exception:
        return False

def remove_monitoring_topic_internal(user_id, topic):
    """Internal function to remove monitoring topic without HTTP wrapper"""
    try:
        user = DatabaseHelpers.get_user_by_id(user_id)
        
        if not user:
            return False
        
        current_prefs = user.get('preferences', {})
        monitoring_topics = current_prefs.get('monitoring_topics', [])
        
        if topic in monitoring_topics:
            monitoring_topics.remove(topic)
            current_prefs['monitoring_topics'] = monitoring_topics
            
            DatabaseHelpers.update_user_preferences(user_id, current_prefs)
            return True
        
        return False
        
    except Exception:
        return False

def analyze_chat_for_preferences(user_id, chat_messages):
    """Use Gemini to analyze chat and extract user preferences"""
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key or not chat_messages or len(chat_messages) < 3:
        return None
    
    # Get recent messages (last 10)
    recent_messages = chat_messages[-10:]
    conversation = "\n".join([f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" for msg in recent_messages])
    
    prompt = f"""
    Analyze this conversation and extract user interests and topics they want to monitor for news.

    Conversation:
    {conversation}

    Extract and respond with ONLY a JSON object containing:
    - interests: array of general interest categories (e.g., "Technology", "Finance", "Remote Work")
    - monitoring_topics: array of specific topics to track (e.g., "Python jobs", "Tesla stock", "AWS updates")
    - relevance_threshold: number 1-100 (how selective they seem to be)
    - summary: brief description of user's news preferences

    Focus on explicit mentions of interests, jobs, companies, or technologies they want updates on.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            
            if data and 'candidates' in data and len(data['candidates']) > 0:
                candidate = data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    gemini_text = candidate['content']['parts'][0]['text']
                    gemini_text = gemini_text.replace('```json', '').replace('```', '').strip()
                    
                    try:
                        analysis = json.loads(gemini_text)
                        
                        # Update user preferences
                        user = DatabaseHelpers.get_user_by_id(user_id)
                        if user:
                            current_prefs = user.get('preferences', {})
                            
                            # Merge new insights with existing preferences
                            new_interests = list(set(current_prefs.get('interests', []) + analysis.get('interests', [])))
                            new_monitoring = list(set(current_prefs.get('monitoring_topics', []) + analysis.get('monitoring_topics', [])))
                            
                            updated_prefs = {
                                **current_prefs,
                                'interests': new_interests,
                                'monitoring_topics': new_monitoring,
                                'relevance_threshold': analysis.get('relevance_threshold', current_prefs.get('relevance_threshold', 75))
                            }
                            
                            DatabaseHelpers.update_user_preferences(user_id, updated_prefs)
                            
                            # Update user memory
                            DatabaseHelpers.update_user_memory(
                                user_id,
                                analysis.get('summary', ''),
                                new_interests
                            )
                            
                            return analysis
                            
                    except Exception:
                        pass
                        
    except Exception:
        pass
    
    return None

def format_conversation_history(messages, limit=10):
    """Format recent messages for AI context"""
    if not messages:
        return "This is the start of our conversation."
    
    # Get last N messages
    recent = messages[-limit:] if len(messages) > limit else messages
    
    formatted = []
    for msg in recent:
        role = "You" if msg.get('role') == 'assistant' else "User"
        content = msg.get('content', '')[:200]  # Truncate long messages
        formatted.append(f"{role}: {content}")
    
    return "\n".join(formatted)

def create_ai_prompt(message_content, user_preferences, conversation_history, user_memory):
    """Create comprehensive AI prompt with context"""
    
    current_monitoring = user_preferences.get('monitoring_topics', [])
    interests = user_preferences.get('interests', [])
    email_enabled = user_preferences.get('email_notifications', False)
    email_frequency = user_preferences.get('email_frequency_hours', 1)
    
    # Handle None email_frequency (database issue)
    if email_frequency is None:
        email_frequency = 1
    
    # Get memory context
    memory_context = ""
    if user_memory and user_memory.get('memorySnapshot'):
        memory_context = f"What I remember about you: {user_memory.get('memorySnapshot')}"
    
    # Email frequency description
    email_desc = "Off"
    if email_enabled:
        if email_frequency == 1:
            email_desc = "Every hour"
        elif email_frequency < 24:
            email_desc = f"Every {email_frequency} hours"
        else:
            email_desc = "Daily"
    
    prompt = f"""You are Canary AI, a friendly and helpful personalized news assistant. You help users track news topics they care about and manage their email notifications.

CONVERSATION CONTEXT:
{conversation_history}

CURRENT USER MESSAGE: "{message_content}"

YOUR MEMORY:
{memory_context or "I'm still learning about your interests."}

CURRENT USER SETTINGS:
- Monitoring topics: {', '.join(current_monitoring) if current_monitoring else 'None yet'}
- General interests: {', '.join(interests) if interests else 'Still discovering'}
- Email notifications: {email_desc}

YOUR CAPABILITIES:
1. Add/remove news monitoring topics when users mention them
2. Turn email notifications on/off and adjust frequency
3. Explain how their news feed changes
4. Help discover new topics to follow
5. Answer questions about news and current events
6. Provide insights about their interests

RESPONSE STYLE:
- Be conversational, friendly, and helpful
- Don't be overly formal or robotic
- Acknowledge when you'll track new topics or stop tracking others
- If they want email changes, be helpful about that
- Reference our conversation history when relevant
- Be concise but informative

Respond naturally to their message, keeping context from our conversation."""

    return prompt

def create_new_chat(event, context):
    """Create a new chat"""
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return {"statusCode": 200, "headers": get_cors_headers(), "body": ""}
        
        user_id = extract_user_from_token(event)
        
        if not user_id:
            return {
                "statusCode": 401,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Unauthorized"})
            }
        
        body = json.loads(event.get('body', '{}'))
        title = body.get('title', 'New Chat')
        
        chat = DatabaseHelpers.create_chat(user_id, title)
        
        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps(chat)
        }
        
    except Exception as e:
        return {"statusCode": 500, "headers": get_cors_headers(), "body": json.dumps({"error": str(e)})}

def get_all_chats(event, context):
    """Get all user chats"""
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return {"statusCode": 200, "headers": get_cors_headers(), "body": ""}
        
        user_id = extract_user_from_token(event)
        
        if not user_id:
            return {
                "statusCode": 401,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Unauthorized"})
            }
        
        chats = DatabaseHelpers.get_user_chats(user_id)
        
        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps(chats)
        }
        
    except Exception as e:
        return {"statusCode": 500, "headers": get_cors_headers(), "body": json.dumps({"error": str(e)})}

def get_chat_by_id(event, context):
    """Get specific chat with messages"""
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return {"statusCode": 200, "headers": get_cors_headers(), "body": ""}
        
        user_id = extract_user_from_token(event)
        
        if not user_id:
            return {
                "statusCode": 401,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Unauthorized"})
            }
        
        path_params = event.get('pathParameters')
        
        if not path_params or not path_params.get('chatId'):
            return {
                "statusCode": 400,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Missing chatId in path"})
            }
        
        chat_id = path_params['chatId']
        
        # Get chat
        chat = DatabaseHelpers.get_chat(chat_id)
        
        if not chat:
            return {
                "statusCode": 404,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Chat not found"})
            }
        
        # Verify ownership
        if chat.get('userId') != user_id:
            return {
                "statusCode": 403,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Access denied"})
            }
        
        # Get messages
        messages = DatabaseHelpers.get_chat_messages(chat_id)
        chat['messages'] = messages
        
        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps(chat)
        }
        
    except Exception as e:
        return {"statusCode": 500, "headers": get_cors_headers(), "body": json.dumps({"error": str(e)})}

def save_message(event, context):
    """Save user message and get AI response with full conversation context"""
    print("=== SAVE MESSAGE STARTED ===")
    try:
        print("1. Checking OPTIONS")
        if event.get('httpMethod') == 'OPTIONS':
            return {"statusCode": 200, "headers": get_cors_headers(), "body": ""}
        
        print("2. Extracting user from token")
        user_id = extract_user_from_token(event)
        print(f"3. User ID: {user_id}")
        
        if not user_id:
            return {
                "statusCode": 401,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Unauthorized"})
            }
        
        print("4. Getting path parameters")
        path_params = event.get('pathParameters')
        print(f"5. Path params: {path_params}")
        
        if not path_params or not path_params.get('chatId'):
            return {
                "statusCode": 400,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Missing chatId in path"})
            }
        
        print("6. Getting chat_id and body")
        chat_id = path_params['chatId']
        body = json.loads(event.get('body', '{}'))
        print(f"7. Chat ID: {chat_id}, Body: {body}")
        
        print("8. Verifying chat exists and user owns it")
        chat = DatabaseHelpers.get_chat(chat_id)
        
        if not chat:
            return {
                "statusCode": 404,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Chat not found"})
            }
        
        if chat.get('userId') != user_id:
            return {
                "statusCode": 403,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Access denied"})
            }
        
        print("9. Saving user message")
        message_content = body.get('content', '')
        print(f"9a. Message content: {message_content}")
        
        user_message = DatabaseHelpers.save_message(
            chat_id, 
            user_id, 
            message_content, 
            'user'
        )
        print(f"10. User message: {user_message}")
        
        if not user_message:
            return {
                "statusCode": 500,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Failed to save user message"})
            }
        
        print("11. Getting user data and context")
        user = DatabaseHelpers.get_user_by_id(user_id)
        
        if not user:
            return {
                "statusCode": 404,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "User not found"})
            }
        
        # Get conversation history BEFORE generating AI response
        print("12. Getting conversation history")
        all_messages = DatabaseHelpers.get_chat_messages(chat_id, limit=20)
        conversation_history = format_conversation_history(all_messages)
        
        # Get user memory
        print("13. Getting user memory")
        user_memory = DatabaseHelpers.get_user_memory(user_id)
        
        user_preferences = user.get('preferences', {})
        print(f"14. User preferences: {user_preferences}")
        
        # FIRST: Check for preference changes from the user message
        print("15. Checking for preference changes")
        temp_conversation = f"User: {message_content}"
        preference_changes = extract_preferences_from_conversation(temp_conversation, user_id)
        email_changes = extract_email_preferences_from_conversation(temp_conversation, user_id)
        print(f"16. Preference changes: {preference_changes}")
        print(f"16a. Email changes: {email_changes}")
        
        # Apply preference changes BEFORE generating AI response
        changes_made = []
        
        # Add new topics
        for topic in preference_changes.get('add', []):
            if add_monitoring_topic_internal(user_id, topic):
                changes_made.append(f"✅ Now tracking: {topic}")
        
        # Remove topics
        for topic in preference_changes.get('remove', []):
            if remove_monitoring_topic_internal(user_id, topic):
                changes_made.append(f"❌ Stopped tracking: {topic}")
        
        # Handle email preference changes
        if email_changes.get('action'):
            email_success, email_changes_list = update_email_preferences_internal(user_id, email_changes)
            if email_success and isinstance(email_changes_list, list):
                changes_made.extend(email_changes_list)
        
        # Get UPDATED user preferences after changes
        updated_user = DatabaseHelpers.get_user_by_id(user_id)
        updated_preferences = updated_user.get('preferences', {}) if updated_user else user_preferences
        
        print("17. Creating AI prompt with full context")
        ai_prompt = create_ai_prompt(
            message_content, 
            updated_preferences, 
            conversation_history, 
            user_memory
        )
        
        print("18. Generating AI response using Gemini")
        api_key = os.environ.get('GEMINI_API_KEY')
        ai_content = ""
        
        if api_key:
            print("18a. API key exists, making Gemini call")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            
            payload = {"contents": [{"parts": [{"text": ai_prompt}]}]}
            
            try:
                print("18b. Sending request to Gemini")
                response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
                print(f"18c. Gemini response status: {response.status_code}")
                
                if response.status_code == 200:
                    print("18d. Gemini success, parsing response")
                    data = response.json()
                    
                    if data and 'candidates' in data and len(data['candidates']) > 0:
                        candidate = data['candidates'][0]
                        
                        if 'content' in candidate and 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                            ai_content = candidate['content']['parts'][0]['text']
                            print(f"18e. Got AI content: {ai_content[:100]}...")
                        else:
                            print("18f. No content in Gemini response")
                            ai_content = "I'm here to help you stay updated on news that matters to you. What topics would you like me to track?"
                    else:
                        print("18g. No candidates in Gemini response")
                        ai_content = "I'm here to help you stay updated on news that matters to you. What topics would you like me to track?"
                else:
                    print(f"18h. Gemini failed: {response.text}")
                    ai_content = "I'm here to help you stay updated on news that matters to you. What topics would you like me to track?"
                    
            except Exception as e:
                print(f"18i. Gemini exception: {str(e)}")
                ai_content = "I'm here to help you stay updated on news that matters to you. What topics would you like me to track?"
        else:
            print("18j. No API key found")
            ai_content = "I'm here to help you stay updated on news that matters to you. What topics would you like me to track?"
        
        print(f"19. AI content: {ai_content}")
        
        # Add preference changes to AI response if any were made
        if changes_made:
            print("20. Adding preference changes to response")
            
            # Get final status for summary
            final_monitoring = updated_preferences.get('monitoring_topics', [])
            email_enabled = updated_preferences.get('email_notifications', False)
            email_frequency = updated_preferences.get('email_frequency_hours', 1)
            
            # Handle None email_frequency
            if email_frequency is None:
                email_frequency = 1
            
            changes_text = "\n".join(changes_made)
            ai_content += f"\n\n{changes_text}"
            
            # Add status summary
            status_parts = []
            if final_monitoring:
                status_parts.append(f"📈 Tracking: {', '.join(final_monitoring)}")
            
            if email_enabled:
                if email_frequency == 1:
                    status_parts.append("📧 Email: Every hour")
                elif email_frequency < 24:
                    status_parts.append(f"📧 Email: Every {email_frequency} hours")
                else:
                    status_parts.append("📧 Email: Daily")
            else:
                status_parts.append("📧 Email: Off")
            
            if status_parts:
                ai_content += f"\n\n**Your settings:** {' | '.join(status_parts)}"
        
        print("21. Saving AI response")
        ai_message = DatabaseHelpers.save_message(
            chat_id, 
            user_id, 
            ai_content, 
            'assistant'
        )
        print(f"22. AI message: {ai_message}")
        
        if not ai_message:
            return {
                "statusCode": 500,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Failed to save AI message"})
            }
        
        print("23. Updating user memory periodically")
        message_count = chat.get('messageCount', 0)
        
        # Update memory more frequently and include recent context
        if message_count % 3 == 0:  # Every 3 messages instead of 5
            try:
                recent_messages = DatabaseHelpers.get_chat_messages(chat_id, limit=10)
                
                if recent_messages:
                    analyze_chat_for_preferences(user_id, recent_messages)
            except Exception as e:
                print(f"Memory update failed: {e}")
        
        # Send email confirmation if needed
        if changes_made and updated_preferences.get('email_notifications', False):
            try:
                send_email_preference_confirmation(
                    user['email'], 
                    user.get('username', user['email'].split('@')[0]),
                    changes_made
                )
            except Exception as e:
                print(f"Email confirmation failed: {e}")
        
        print("24. Returning AI message")
        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps(ai_message)
        }
        
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"TRACEBACK: {traceback.format_exc()}")
        return {"statusCode": 500, "headers": get_cors_headers(), "body": json.dumps({"error": str(e)})}

def get_ai_memory(event, context):
    """Get AI memory for user"""
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return {"statusCode": 200, "headers": get_cors_headers(), "body": ""}
        
        user_id = extract_user_from_token(event)
        
        if not user_id:
            return {
                "statusCode": 401,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Unauthorized"})
            }
        
        user = DatabaseHelpers.get_user_by_id(user_id)
        
        if not user:
            return {
                "statusCode": 404,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "User not found"})
            }
        
        user_preferences = user.get('preferences', {})
        user_memory = DatabaseHelpers.get_user_memory(user_id)
        
        interests_summary = ", ".join(user_preferences.get('interests', [])).lower()
        monitoring_topics = user_preferences.get('monitoring_topics', [])
        
        # Handle memory data safely
        memory_snapshot = ""
        last_updated = datetime.now().isoformat() + "Z"
        
        if user_memory:
            memory_snapshot = user_memory.get('memorySnapshot', '')
            last_updated = user_memory.get('lastUpdated', last_updated)
        
        if not memory_snapshot:
            if interests_summary:
                memory_snapshot = f"You're interested in {interests_summary} and like staying updated on current trends. I'm keeping track of the topics you care about most."
            else:
                memory_snapshot = "I'm learning about your interests as we chat. Tell me what topics you'd like to stay updated on!"
        
        memory_data = {
            "summary": memory_snapshot,
            "active_monitoring": monitoring_topics,
            "interests": user_preferences.get('interests', []),
            "last_updated": last_updated,
            "monitoring_count": len(monitoring_topics)
        }
        
        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps(memory_data)
        }
        
    except Exception as e:
        return {"statusCode": 500, "headers": get_cors_headers(), "body": json.dumps({"error": str(e)})}
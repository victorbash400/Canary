# email_preference_handlers.py - Natural language email preference handling

import json
import requests
import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError
from db_helpers import DatabaseHelpers
from utils import get_cors_headers, extract_user_from_token

# Initialize SES client
ses_client = boto3.client('ses', region_name='eu-north-1')

def extract_email_preferences_from_conversation(conversation_text, user_id):
    """Extract email preference changes from conversation using Gemini"""
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key:
        return {"action": None}
    
    prompt = f"""
    Analyze this conversation and extract any EMAIL NOTIFICATION preferences the user wants to change.

    Conversation: {conversation_text}

    Look for phrases about EMAIL specifically:
    - "email me updates", "send me notifications", "email notifications"
    - "every 4 hours", "twice a day", "hourly updates", "daily digest"
    - "stop emailing", "turn off notifications", "no more emails"
    - "more frequent", "less spam", "reduce emails"
    - "urgent only", "important news only", "breaking news"

    Return ONLY a JSON object with this exact format:
    {{
        "action": "enable|disable|change_frequency|null",
        "frequency_hours": 6,
        "urgent_only": false,
        "reasoning": "what the user said about emails"
    }}

    Rules:
    - If they mention email/notifications with time (2 hours, daily, etc) → action: "change_frequency"
    - If they want to start getting emails → action: "enable"  
    - If they want to stop emails → action: "disable"
    - If no email mention → action: null
    - frequency_hours: convert their request to hours (daily=24, twice daily=12, hourly=1, etc)
    - urgent_only: true if they only want breaking/urgent news
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
                        email_changes = json.loads(gemini_text)
                        return email_changes
                    except Exception:
                        return {"action": None}
                else:
                    return {"action": None}
            else:
                return {"action": None}
        else:
            return {"action": None}
                
    except Exception:
        return {"action": None}

def update_email_preferences_internal(user_id, email_changes):
    """Internal function to update email preferences"""
    try:
        user = DatabaseHelpers.get_user_by_id(user_id)
        if not user:
            return False, "User not found"
        
        current_prefs = user.get('preferences', {})
        action = email_changes.get('action')
        
        changes_made = []
        
        if action == 'enable':
            current_prefs['email_notifications'] = True
            current_prefs['email_frequency_hours'] = email_changes.get('frequency_hours', 6)
            if email_changes.get('urgent_only'):
                current_prefs['urgent_only'] = True
            changes_made.append("✅ Email notifications enabled")
            
        elif action == 'disable':
            current_prefs['email_notifications'] = False
            changes_made.append("❌ Email notifications disabled")
            
        elif action == 'change_frequency':
            frequency = email_changes.get('frequency_hours', 6)
            # Clamp between 1 and 24 hours
            frequency = max(1, min(24, frequency))
            current_prefs['email_frequency_hours'] = frequency
            
            if frequency == 1:
                changes_made.append(f"⏰ Email frequency set to every hour")
            elif frequency < 24:
                changes_made.append(f"⏰ Email frequency set to every {frequency} hours")
            else:
                changes_made.append(f"⏰ Email frequency set to daily")
            
            # Enable notifications if they're setting frequency
            if not current_prefs.get('email_notifications', False):
                current_prefs['email_notifications'] = True
                changes_made.append("✅ Email notifications enabled")
        
        if changes_made:
            success = DatabaseHelpers.update_user_preferences(user_id, current_prefs)
            if success:
                return True, changes_made
        
        return False, "No changes needed"
        
    except Exception as e:
        return False, f"Error updating preferences: {str(e)}"

def generate_welcome_email_html(user_name, user_email):
    """Generate welcome email HTML"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Canary AI</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 32px; font-weight: 600; }}
            .header p {{ margin: 15px 0 0 0; opacity: 0.9; font-size: 18px; }}
            .content {{ padding: 40px 30px; }}
            .greeting {{ font-size: 20px; color: #374151; margin-bottom: 25px; }}
            .feature {{ background: #f8fafc; padding: 20px; border-radius: 12px; margin: 20px 0; border-left: 4px solid #667eea; }}
            .feature h3 {{ margin: 0 0 10px 0; color: #1f2937; font-size: 18px; }}
            .feature p {{ margin: 0; color: #6b7280; line-height: 1.6; }}
            .cta-button {{ background: #667eea; color: white; padding: 15px 30px; border-radius: 8px; text-decoration: none; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }}
            .spam-notice {{ background: #fef3c7; border: 1px solid #f59e0b; color: #92400e; padding: 20px; border-radius: 8px; margin: 25px 0; }}
            .spam-notice h4 {{ margin: 0 0 10px 0; font-size: 16px; }}
            .footer {{ background-color: #f9fafb; padding: 30px 20px; text-align: center; color: #6b7280; }}
            .emoji {{ font-size: 24px; margin-right: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🐦 Welcome to Canary AI!</h1>
                <p>Your intelligent news companion is ready</p>
            </div>
            
            <div class="content">
                <div class="greeting">
                    Hey {user_name}! 👋
                </div>
                
                <p style="font-size: 16px; line-height: 1.6; color: #374151; margin-bottom: 25px;">
                    Welcome to Canary AI! I'm excited to help you stay on top of the news that matters most to you. 
                    Think of me as your personal news curator who learns what you care about and brings you the most relevant updates.
                </p>
                
                <div class="feature">
                    <h3><span class="emoji">🎯</span>Smart News Curation</h3>
                    <p>Just tell me what topics you're interested in through our chat, and I'll automatically start tracking them for you. No complicated setup required!</p>
                </div>
                
                <div class="feature">
                    <h3><span class="emoji">💬</span>Natural Conversations</h3>
                    <p>Say things like "track Tesla stock" or "email me AI updates every 4 hours" and I'll understand exactly what you want.</p>
                </div>
                
                <div class="feature">
                    <h3><span class="emoji">📧</span>Smart Email Digests</h3>
                    <p>I'll send you personalized email updates when there's actually something worth your attention. No spam, just the good stuff.</p>
                </div>
                
                <div style="text-align: center;">
                    <a href="{os.environ.get('FRONTEND_URL', '#')}" class="cta-button">Start Chatting with Canary →</a>
                </div>
                
                <div class="spam-notice">
                    <h4>📬 Important: Check Your Spam Folder!</h4>
                    <p>
                        Since this is our first email to you, it might end up in your spam/junk folder. 
                        Please check there and mark this email as "Not Spam" to ensure you receive future updates. 
                        This helps your email provider recognize that you want to hear from Canary AI!
                    </p>
                </div>
                
                <p style="font-size: 14px; color: #6b7280; margin-top: 30px;">
                    <strong>Quick Start Tips:</strong><br>
                    • Chat with me about your interests and I'll start tracking them<br>
                    • Say "email me updates" to get personalized news digests<br>
                    • Ask me to adjust email frequency anytime: "email me every 2 hours"<br>
                    • Tell me to stop anytime: "turn off email notifications"
                </p>
            </div>
            
            <div class="footer">
                <p>You're receiving this welcome email because you just signed up for Canary AI.</p>
                <p style="margin-top: 15px; font-size: 12px;">
                    Canary AI • Intelligent News Curation<br>
                    Built with 💜 for staying informed
                </p>
            </div>
        </div>
    </body>
    </html>
    """

def generate_welcome_email_text(user_name):
    """Generate plain text version of welcome email"""
    return f"""
    WELCOME TO CANARY AI!
    
    Hey {user_name}!
    
    Welcome to Canary AI! I'm excited to help you stay on top of the news that matters most to you. Think of me as your personal news curator who learns what you care about and brings you the most relevant updates.
    
    HERE'S WHAT I CAN DO:
    
    🎯 SMART NEWS CURATION
    Just tell me what topics you're interested in through our chat, and I'll automatically start tracking them for you. No complicated setup required!
    
    💬 NATURAL CONVERSATIONS  
    Say things like "track Tesla stock" or "email me AI updates every 4 hours" and I'll understand exactly what you want.
    
    📧 SMART EMAIL DIGESTS
    I'll send you personalized email updates when there's actually something worth your attention. No spam, just the good stuff.
    
    ⚠️ IMPORTANT: CHECK YOUR SPAM FOLDER!
    Since this is our first email to you, it might end up in your spam/junk folder. Please check there and mark this email as "Not Spam" to ensure you receive future updates.
    
    QUICK START TIPS:
    • Chat with me about your interests and I'll start tracking them
    • Say "email me updates" to get personalized news digests  
    • Ask me to adjust email frequency anytime: "email me every 2 hours"
    • Tell me to stop anytime: "turn off email notifications"
    
    Start chatting: {os.environ.get('FRONTEND_URL', 'https://yourcanaryapp.com')}
    
    Welcome aboard!
    Canary AI
    """

def send_welcome_email(user_email, user_name):
    """Send welcome email to new user"""
    try:
        html_content = generate_welcome_email_html(user_name, user_email)
        text_content = generate_welcome_email_text(user_name)
        
        response = ses_client.send_email(
            Destination={'ToAddresses': [user_email]},
            Message={
                'Body': {
                    'Html': {'Charset': 'UTF-8', 'Data': html_content},
                    'Text': {'Charset': 'UTF-8', 'Data': text_content}
                },
                'Subject': {'Charset': 'UTF-8', 'Data': '🐦 Welcome to Canary AI - Your intelligent news companion!'}
            },
            Source=os.environ.get('SES_SENDER_EMAIL', 'noreply@yourcanaryapp.com')
        )
        
        print(f"Welcome email sent to {user_email}. MessageId: {response['MessageId']}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"Welcome email failed for {user_email}: {error_code}")
        
        # Common SES errors and what they mean
        if error_code == 'MessageRejected':
            print("Email address not verified or invalid")
        elif error_code == 'SendingPausedException':
            print("SES sending paused - check AWS console")
        elif error_code == 'MailFromDomainNotVerifiedException':
            print("Sender domain not verified in SES")
        
        return False
    except Exception as e:
        print(f"Welcome email error for {user_email}: {e}")
        return False

def send_email_preference_confirmation(user_email, user_name, changes_made):
    """Send confirmation when email preferences are updated"""
    try:
        changes_text = "<br>".join(changes_made)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f8fafc; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 25px; }}
                .header h1 {{ color: #1f2937; margin: 0; font-size: 24px; }}
                .changes {{ background: #f0f9ff; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; }}
                .footer {{ text-align: center; margin-top: 25px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🐦 Email Preferences Updated</h1>
                </div>
                
                <p>Hey {user_name}!</p>
                
                <p>I've updated your email notification preferences based on our conversation:</p>
                
                <div class="changes">
                    {changes_text}
                </div>
                
                <p>You can always adjust these by chatting with me anytime. Just say something like "email me every 2 hours" or "turn off notifications".</p>
                
                <div class="footer">
                    <p>Canary AI • Your intelligent news companion</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        EMAIL PREFERENCES UPDATED
        
        Hey {user_name}!
        
        I've updated your email notification preferences:
        
        {chr(10).join(changes_made)}
        
        You can always adjust these by chatting with me anytime.
        
        Canary AI
        """
        
        response = ses_client.send_email(
            Destination={'ToAddresses': [user_email]},
            Message={
                'Body': {
                    'Html': {'Charset': 'UTF-8', 'Data': html_content},
                    'Text': {'Charset': 'UTF-8', 'Data': text_content}
                },
                'Subject': {'Charset': 'UTF-8', 'Data': '🐦 Canary AI: Email preferences updated'}
            },
            Source=os.environ.get('SES_SENDER_EMAIL', 'noreply@yourcanaryapp.com')
        )
        
        print(f"Preference confirmation sent to {user_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send preference confirmation to {user_email}: {e}")
        return False
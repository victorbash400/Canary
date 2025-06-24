# email_digest_system.py - Smart email scheduling and delivery

import json
import os
import boto3
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore.exceptions import ClientError
from db_helpers import DatabaseHelpers
from news_handlers import fetch_topic_news

# Initialize SES client
ses_client = boto3.client('ses', region_name='eu-north-1')

def should_send_digest_to_user(user):
    """Check if user should receive digest now based on their frequency"""
    try:
        preferences = user.get('preferences', {})
        
        # Check if email notifications are enabled
        if not preferences.get('email_notifications', False):
            return False
        
        # Get frequency (default 6 hours)
        frequency_hours = preferences.get('email_frequency_hours', 6)
        
        # Get last email sent time (if any)
        last_email_sent = preferences.get('last_email_sent')
        
        if not last_email_sent:
            # Never sent email before, send now
            return True
        
        # Parse last sent time
        last_sent_dt = datetime.fromisoformat(last_email_sent.replace('Z', '+00:00'))
        now = datetime.now().replace(tzinfo=last_sent_dt.tzinfo)
        
        # Check if enough time has passed
        time_diff = now - last_sent_dt
        return time_diff.total_seconds() >= (frequency_hours * 3600)
        
    except Exception as e:
        print(f"Error checking digest schedule for user: {e}")
        return False

def ask_gemini_if_worth_emailing(articles, user_interests, user_name):
    """Ask Gemini if this batch of articles is worth emailing"""
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key or not articles:
        return False, "No content to evaluate"
    
    # Prepare article summaries for Gemini
    article_summaries = []
    for article in articles[:5]:  # Limit to top 5 for evaluation
        summary = f"Title: {article.get('title', 'No title')}\n"
        summary += f"Summary: {article.get('summary', 'No summary')[:200]}...\n"
        summary += f"Relevance Score: {article.get('relevanceScore', 0)}%\n"
        summary += f"Urgency: {article.get('urgency', 'medium')}\n"
        article_summaries.append(summary)
    
    articles_text = "\n---\n".join(article_summaries)
    
    prompt = f"""
    You are Canary AI's email gatekeeper. Decide if these news articles are worth interrupting {user_name} with an email.

    User's interests: {user_interests}
    
    Articles to evaluate:
    {articles_text}

    Criteria for sending email:
    - At least one article is highly relevant (80+ relevance score) 
    - OR there's urgent/breaking news (urgency: high)
    - OR multiple moderately relevant articles (70+ score) about their interests
    - Don't send for: routine updates, low relevance content, or repetitive news

    Respond with ONLY a JSON object:
    {{
        "should_send": true/false,
        "reason": "brief explanation why/why not",
        "urgency_level": "low/medium/high",
        "top_article_title": "most important article title"
    }}

    Be selective - only send if the user would genuinely want to be interrupted.
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
                        decision = json.loads(gemini_text)
                        should_send = decision.get('should_send', False)
                        reason = decision.get('reason', 'No reason provided')
                        return should_send, reason
                    except Exception:
                        return False, "Failed to parse Gemini response"
        
        return False, "Gemini API error"
                
    except Exception as e:
        print(f"Gemini evaluation error: {e}")
        return False, f"Error: {str(e)}"

def generate_digest_email_html(articles, user_name, digest_reason):
    """Generate HTML email for news digest"""
    urgent_articles = [a for a in articles if a.get('urgency') == 'high']
    regular_articles = [a for a in articles if a.get('urgency') != 'high']
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Canary News Update</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px 20px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
            .header p {{ margin: 8px 0 0 0; opacity: 0.9; font-size: 14px; }}
            .content {{ padding: 25px 20px; }}
            .greeting {{ font-size: 16px; color: #374151; margin-bottom: 20px; }}
            .reason {{ background: #f0f9ff; padding: 15px; border-radius: 8px; margin-bottom: 25px; border-left: 4px solid #3b82f6; }}
            .reason p {{ margin: 0; color: #1e40af; font-size: 14px; }}
            .section {{ margin-bottom: 30px; }}
            .section-title {{ font-size: 18px; font-weight: 600; color: #1f2937; margin-bottom: 15px; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; }}
            .urgent-title {{ color: #dc2626; border-bottom-color: #dc2626; }}
            .article {{ border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 15px; overflow: hidden; }}
            .article-image {{ width: 100%; height: 150px; object-fit: cover; }}
            .article-content {{ padding: 15px; }}
            .article-title {{ font-size: 16px; font-weight: 600; color: #1f2937; margin-bottom: 8px; line-height: 1.4; }}
            .article-title a {{ color: inherit; text-decoration: none; }}
            .article-title a:hover {{ color: #667eea; }}
            .article-summary {{ color: #6b7280; line-height: 1.5; margin-bottom: 12px; font-size: 14px; }}
            .article-meta {{ display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #9ca3af; }}
            .relevance-score {{ background: #f3f4f6; padding: 2px 6px; border-radius: 10px; font-weight: 500; }}
            .urgent-badge {{ background: #fee2e2; color: #dc2626; padding: 2px 6px; border-radius: 10px; font-weight: 500; }}
            .footer {{ background-color: #f9fafb; padding: 20px; text-align: center; color: #6b7280; font-size: 12px; }}
            .footer a {{ color: #667eea; text-decoration: none; }}
            .cta-button {{ background: #667eea; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; display: inline-block; margin: 15px 0; font-weight: 500; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🐦 News Update from Canary</h1>
                <p>Curated specifically for you</p>
            </div>
            
            <div class="content">
                <div class="greeting">
                    Hi {user_name}! 👋
                </div>
                
                <div class="reason">
                    <p><strong>Why you're getting this:</strong> {digest_reason}</p>
                </div>
    """
    
    # Add urgent articles if any
    if urgent_articles:
        html_content += """
                <div class="section">
                    <h2 class="section-title urgent-title">🚨 Urgent Updates</h2>
        """
        for article in urgent_articles[:2]:  # Max 2 urgent
            html_content += f"""
                    <div class="article">
                        <img src="{article.get('imageUrl', '')}" alt="Article Image" class="article-image" onerror="this.style.display='none'">
                        <div class="article-content">
                            <h3 class="article-title">
                                <a href="{article.get('url', '#')}">{article.get('title', 'No Title')}</a>
                            </h3>
                            <p class="article-summary">{article.get('summary', '')[:150]}...</p>
                            <div class="article-meta">
                                <span>{article.get('source', 'Canary AI')}</span>
                                <div>
                                    <span class="urgent-badge">URGENT</span>
                                    <span class="relevance-score">{article.get('relevanceScore', 0)}%</span>
                                </div>
                            </div>
                        </div>
                    </div>
            """
        html_content += "</div>"
    
    # Add regular articles
    if regular_articles:
        html_content += """
                <div class="section">
                    <h2 class="section-title">📰 Your Personalized Updates</h2>
        """
        for article in regular_articles[:4]:  # Max 4 regular
            html_content += f"""
                    <div class="article">
                        <img src="{article.get('imageUrl', '')}" alt="Article Image" class="article-image" onerror="this.style.display='none'">
                        <div class="article-content">
                            <h3 class="article-title">
                                <a href="{article.get('url', '#')}">{article.get('title', 'No Title')}</a>
                            </h3>
                            <p class="article-summary">{article.get('summary', '')[:150]}...</p>
                            <div class="article-meta">
                                <span>{article.get('source', 'Canary AI')}</span>
                                <span class="relevance-score">{article.get('relevanceScore', 0)}%</span>
                            </div>
                        </div>
                    </div>
            """
        html_content += "</div>"
    
    # Footer
    html_content += f"""
                <div style="text-align: center; margin: 25px 0;">
                    <a href="{os.environ.get('FRONTEND_URL', '#')}/news" class="cta-button">View All News →</a>
                </div>
            </div>
            
            <div class="footer">
                <p>Sent at {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}</p>
                <p>
                    <a href="{os.environ.get('FRONTEND_URL', '#')}/chat">Chat with Canary</a> | 
                    <a href="{os.environ.get('FRONTEND_URL', '#')}/preferences">Update Preferences</a>
                </p>
                <p style="margin-top: 15px; font-size: 11px;">
                    You're receiving this because you enabled email notifications in Canary AI.<br>
                    To change frequency or stop emails, just chat with me and say "change email settings"
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def generate_digest_email_text(articles, user_name, digest_reason):
    """Generate plain text version of digest email"""
    urgent_articles = [a for a in articles if a.get('urgency') == 'high']
    regular_articles = [a for a in articles if a.get('urgency') != 'high']
    
    text_content = f"""
CANARY AI NEWS UPDATE

Hi {user_name}!

Why you're getting this: {digest_reason}

"""
    
    if urgent_articles:
        text_content += "🚨 URGENT UPDATES:\n" + "="*30 + "\n\n"
        for article in urgent_articles[:2]:
            text_content += f"• {article.get('title', 'No Title')}\n"
            text_content += f"  {article.get('summary', '')[:120]}...\n"
            text_content += f"  Relevance: {article.get('relevanceScore', 0)}% | Source: {article.get('source', 'Canary AI')}\n"
            text_content += f"  Read more: {article.get('url', '#')}\n\n"
    
    if regular_articles:
        text_content += "📰 YOUR PERSONALIZED UPDATES:\n" + "="*35 + "\n\n"
        for article in regular_articles[:4]:
            text_content += f"• {article.get('title', 'No Title')}\n"
            text_content += f"  {article.get('summary', '')[:120]}...\n"
            text_content += f"  Relevance: {article.get('relevanceScore', 0)}% | Source: {article.get('source', 'Canary AI')}\n"
            text_content += f"  Read more: {article.get('url', '#')}\n\n"
    
    text_content += f"""
View all news: {os.environ.get('FRONTEND_URL', 'https://yourcanaryapp.com')}/news
Chat with Canary: {os.environ.get('FRONTEND_URL', 'https://yourcanaryapp.com')}/chat

To change email frequency or stop notifications, just chat with me and say "change email settings"

Sent at {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}
Canary AI - Your intelligent news companion
"""
    
    return text_content

def send_news_digest_email(user_email, articles, user_name, digest_reason):
    """Send news digest email to user"""
    try:
        if not articles:
            return False
        
        # Generate email content
        html_content = generate_digest_email_html(articles, user_name, digest_reason)
        text_content = generate_digest_email_text(articles, user_name, digest_reason)
        
        # Create subject line
        urgent_count = len([a for a in articles if a.get('urgency') == 'high'])
        if urgent_count > 0:
            subject = f"🚨 {urgent_count} Urgent Update{'s' if urgent_count > 1 else ''} from Canary"
        else:
            subject = f"📰 {len(articles)} News Update{'s' if len(articles) > 1 else ''} from Canary"
        
        # Send email
        response = ses_client.send_email(
            Destination={'ToAddresses': [user_email]},
            Message={
                'Body': {
                    'Html': {'Charset': 'UTF-8', 'Data': html_content},
                    'Text': {'Charset': 'UTF-8', 'Data': text_content}
                },
                'Subject': {'Charset': 'UTF-8', 'Data': subject}
            },
            Source=os.environ.get('SES_SENDER_EMAIL', 'noreply@yourcanaryapp.com')
        )
        
        print(f"Digest email sent to {user_email}. MessageId: {response['MessageId']}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"Digest email failed for {user_email}: {error_code}")
        return False
    except Exception as e:
        print(f"Digest email error for {user_email}: {e}")
        return False

def update_user_last_email_sent(user_id):
    """Update when user was last sent an email"""
    try:
        user = DatabaseHelpers.get_user_by_id(user_id)
        if user:
            current_prefs = user.get('preferences', {})
            current_prefs['last_email_sent'] = datetime.now().isoformat() + "Z"
            DatabaseHelpers.update_user_preferences(user_id, current_prefs)
    except Exception as e:
        print(f"Error updating last email sent for user {user_id}: {e}")

def process_user_for_digest(user):
    """Process a single user for email digest"""
    try:
        user_id = user['userId']
        user_email = user['email']
        user_name = user.get('username', user_email.split('@')[0])
        
        print(f"Processing digest for: {user_email}")
        
        # Check if user should receive digest now
        if not should_send_digest_to_user(user):
            print(f"Skipping {user_email} - not time for digest yet")
            return False
        
        # Get user preferences
        preferences = user.get('preferences', {})
        monitoring_topics = preferences.get('monitoring_topics', ['Technology'])
        user_interests = preferences.get('interests', ['Technology'])
        urgent_only = preferences.get('urgent_only', False)
        
        # Fetch news for user's topics
        perplexity_key = os.environ.get('PERPLEXITY_API_KEY')
        if not perplexity_key:
            print("No Perplexity API key found")
            return False
        
        articles = []
        topics_to_process = monitoring_topics[:4]  # Limit for email
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_topic = {
                executor.submit(fetch_topic_news, topic, perplexity_key, user_interests): topic 
                for topic in topics_to_process
            }
            
            for future in as_completed(future_to_topic):
                try:
                    article = future.result(timeout=15)
                    if article:
                        articles.append(article)
                except Exception as e:
                    print(f"Error fetching news: {e}")
        
        if not articles:
            print(f"No articles found for {user_email}")
            return False
        
        # Filter by relevance threshold
        relevance_threshold = preferences.get('relevance_threshold', 75)
        filtered_articles = [a for a in articles if a.get('relevanceScore', 0) >= relevance_threshold]
        
        # If urgent_only, filter for urgent articles
        if urgent_only:
            filtered_articles = [a for a in filtered_articles if a.get('urgency') == 'high']
        
        if not filtered_articles:
            print(f"No relevant articles for {user_email}")
            return False
        
        # Sort by relevance and limit
        filtered_articles.sort(key=lambda x: x.get('relevanceScore', 0), reverse=True)
        final_articles = filtered_articles[:6]  # Max 6 articles per email
        
        # Ask Gemini if this batch is worth emailing
        should_send, reason = ask_gemini_if_worth_emailing(final_articles, user_interests, user_name)
        
        if not should_send:
            print(f"Gemini says skip {user_email}: {reason}")
            return False
        
        # Send the email
        success = send_news_digest_email(user_email, final_articles, user_name, reason)
        
        if success:
            # Update last email sent time
            update_user_last_email_sent(user_id)
            print(f"Successfully sent digest to {user_email}")
            return True
        else:
            print(f"Failed to send digest to {user_email}")
            return False
            
    except Exception as e:
        print(f"Error processing digest for {user.get('email', 'unknown')}: {e}")
        return False

def get_users_for_email_check():
    """Get all users who have email notifications enabled"""
    try:
        # Scan for users with email notifications enabled
        response = DatabaseHelpers.users_table.scan(
            FilterExpression="preferences.email_notifications = :enabled",
            ExpressionAttributeValues={":enabled": True}
        )
        
        return response.get('Items', [])
        
    except Exception as e:
        print(f"Error getting users for email check: {e}")
        return []

# Lambda function for hourly email check
def hourly_email_check(event, context):
    """Lambda function that runs hourly to check who needs email updates"""
    try:
        print("Starting hourly email check...")
        
        # Get all users with email notifications enabled
        users_to_check = get_users_for_email_check()
        print(f"Found {len(users_to_check)} users with email notifications enabled")
        
        if not users_to_check:
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "No users to check for email updates"})
            }
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        # Process users in smaller batches to avoid timeouts
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            for user in users_to_check:
                future = executor.submit(process_user_for_digest, user)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=25)
                    if result:
                        success_count += 1
                    else:
                        skip_count += 1
                except Exception as e:
                    print(f"Error processing user: {e}")
                    error_count += 1
        
        print(f"Email check complete. Sent: {success_count}, Skipped: {skip_count}, Errors: {error_count}")
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Hourly email check completed",
                "emails_sent": success_count,
                "users_skipped": skip_count,
                "errors": error_count,
                "total_users_checked": len(users_to_check)
            })
        }
        
    except Exception as e:
        print(f"Hourly email check error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
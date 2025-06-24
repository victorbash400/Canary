# news_handlers.py - News related functions with parallel processing

import json
import requests
import os
import uuid
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from db_helpers import DatabaseHelpers
from utils import get_cors_headers, extract_user_from_token, get_unsplash_image, analyze_article_with_gemini

def categorize_article_content(article_content, topic):
    """Categorize article using Gemini API - accepts any category"""
    try:
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return "General"
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        prompt = f"""
        Analyze this news article and categorize it into the most appropriate category.

        Return a single, clear category name that best describes the content. Examples include:
        - Technology (AI, software, gadgets, tech companies)
        - Business (corporate news, mergers, industry trends)
        - Finance (markets, stocks, banking, investments)
        - Career (jobs, hiring, workplace trends)
        - Health (medical, wellness, pharmaceuticals)
        - Sports (athletics, competitions, fitness)
        - Entertainment (movies, music, celebrity news)
        - Science (research, discoveries, environment)
        - Politics (elections, government, policy)
        - Agriculture (farming, food production, crops)
        - Education (schools, learning, academic)
        - Travel (tourism, transportation, destinations)
        - Food (cuisine, restaurants, cooking)
        - Fashion (clothing, style, beauty)
        - Real Estate (property, housing, construction)
        - Energy (oil, renewable, utilities)
        - Automotive (cars, transportation, mobility)
        
        Or any other appropriate category that fits the content.

        Topic: {topic}
        Article Content: {article_content[:1000]}

        Return ONLY the category name (e.g., "Agriculture" or "Entertainment").
        """
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and 'candidates' in data and len(data['candidates']) > 0:
                candidate = data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    category = candidate['content']['parts'][0]['text'].strip()
                    
                    # Clean up the category name
                    # Remove quotes, newlines, extra text
                    category = category.replace('"', '').replace("'", "").strip()
                    if '\n' in category:
                        category = category.split('\n')[0].strip()
                    
                    # Capitalize first letter for consistency
                    if category:
                        category = category[0].upper() + category[1:].lower() if len(category) > 1 else category.upper()
                        return category
                    
        # Fallback categorization based on topic keywords
        topic_lower = topic.lower()
        if any(word in topic_lower for word in ["ai", "tech", "software", "startup", "programming"]):
            return "Technology"
        elif any(word in topic_lower for word in ["business", "company", "corporate"]):
            return "Business"
        elif any(word in topic_lower for word in ["finance", "stock", "investment", "crypto"]):
            return "Finance"
        elif any(word in topic_lower for word in ["job", "career", "hiring", "work"]):
            return "Career"
        elif any(word in topic_lower for word in ["health", "medical", "wellness"]):
            return "Health"
        elif any(word in topic_lower for word in ["sport", "athletic", "fitness"]):
            return "Sports"
        elif any(word in topic_lower for word in ["food", "restaurant", "cooking"]):
            return "Food"
        elif any(word in topic_lower for word in ["travel", "tourism", "vacation"]):
            return "Travel"
        elif any(word in topic_lower for word in ["agriculture", "farming", "crops"]):
            return "Agriculture"
        
        return "General"
        
    except Exception as e:
        print(f"Error categorizing article: {e}")
        return "General"

def fetch_topic_news(topic, perplexity_key, user_interests):
    """Fetch news for a single topic"""
    try:
        url = "https://api.perplexity.ai/chat/completions"
        payload = {
            "model": "sonar",
            "messages": [{"role": "user", "content": f"Latest news about {topic} in 2025"}],
            "max_tokens": 400
        }
        headers = {
            "Authorization": f"Bearer {perplexity_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            article_content = data['choices'][0]['message']['content']
            
            # Get Gemini analysis
            gemini_analysis = analyze_article_with_gemini(article_content, topic, user_interests)
            
            # Categorize the article dynamically
            article_category = categorize_article_content(article_content, topic)
            
            # Convert relevance_score to int if it's a string
            relevance_score = gemini_analysis.get("relevance_score", 75)
            if isinstance(relevance_score, str):
                try:
                    relevance_score = int(relevance_score)
                except:
                    relevance_score = 75
            
            article = {
                "id": str(uuid.uuid4()),
                "title": f"Latest: {topic.title()}",
                "summary": gemini_analysis.get("personalized_summary", "AI-curated news summary"),
                "source": "Canary AI News",
                "publishedAt": datetime.now().isoformat() + "Z",
                "url": data.get('citations', ['#'])[0] if data.get('citations') else '#',
                "category": article_category,  # Now using dynamic categorization!
                "relevanceScore": relevance_score,
                "urgency": "high" if relevance_score > 85 else "medium",
                "imageUrl": get_unsplash_image(topic),
                "tags": topic.split(),
                "content": article_content,
                "citations": data.get('citations', []),
                "gemini_analysis": gemini_analysis
            }
            
            print(f"DEBUG: Topic '{topic}' categorized as '{article_category}'")
            
            return article
            
    except Exception as e:
        print(f"Error fetching news for {topic}: {e}")
        return None

def get_news_feed(event, context):
    """Get personalized news feed with parallel processing"""
    try:
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
        monitoring_topics = user_preferences.get('monitoring_topics', ["Technology", "AI", "Current Events"])
        user_interests = user_preferences.get('interests', ["Technology"])
        
        print(f"DEBUG: User preferences: {user_preferences}")
        print(f"DEBUG: Monitoring topics: {monitoring_topics}")
        
        perplexity_key = os.environ.get('PERPLEXITY_API_KEY')
        if not perplexity_key:
            return {"statusCode": 500, "headers": get_cors_headers(), "body": json.dumps({"error": "API key not configured"})}
        
        # Limit to 8 topics for better performance
        topics_to_process = monitoring_topics[:8]
        
        # Use ThreadPoolExecutor for parallel API calls
        all_articles = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            # Submit all tasks
            future_to_topic = {
                executor.submit(fetch_topic_news, topic, perplexity_key, user_interests): topic 
                for topic in topics_to_process
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_topic):
                topic = future_to_topic[future]
                try:
                    article = future.result(timeout=20)  # 20 second timeout per topic
                    if article:
                        all_articles.append(article)
                except Exception as e:
                    print(f"Error processing {topic}: {e}")
        
        # Sort by relevance
        all_articles.sort(key=lambda x: x['relevanceScore'], reverse=True)
        
        print(f"DEBUG: Generated {len(all_articles)} articles")
        for article in all_articles:
            print(f"DEBUG: '{article['title']}' -> Category: {article['category']}")
        
        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps(all_articles)
        }
        
    except Exception as e:
        print(f"News feed error: {e}")
        return {
            "statusCode": 500,
            "headers": get_cors_headers(),
            "body": json.dumps({"error": str(e)})
        }

def get_user_preferences(event, context):
    """Get user preferences"""
    try:
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
        
        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps(user.get('preferences', {}))
        }
        
    except Exception as e:
        return {"statusCode": 500, "headers": get_cors_headers(), "body": json.dumps({"error": str(e)})}

def update_user_preferences(event, context):
    """Update user preferences"""
    try:
        user_id = extract_user_from_token(event)
        if not user_id:
            return {
                "statusCode": 401,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Unauthorized"})
            }
        
        body = json.loads(event.get('body', '{}'))
        
        user = DatabaseHelpers.get_user_by_id(user_id)
        if not user:
            return {
                "statusCode": 404,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "User not found"})
            }
        
        current_prefs = user.get('preferences', {})
        current_prefs.update(body)
        
        DatabaseHelpers.update_user_preferences(user_id, current_prefs)
        
        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps(current_prefs)
        }
        
    except Exception as e:
        return {"statusCode": 500, "headers": get_cors_headers(), "body": json.dumps({"error": str(e)})}

def add_monitoring_topic(event, context):
    """Add monitoring topic"""
    try:
        user_id = extract_user_from_token(event)
        if not user_id:
            return {
                "statusCode": 401,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Unauthorized"})
            }
        
        body = json.loads(event.get('body', '{}'))
        topic = body.get('topic')
        
        user = DatabaseHelpers.get_user_by_id(user_id)
        if not user:
            return {
                "statusCode": 404,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "User not found"})
            }
        
        current_prefs = user.get('preferences', {})
        monitoring_topics = current_prefs.get('monitoring_topics', [])
        
        if topic and topic not in monitoring_topics:
            monitoring_topics.append(topic)
            current_prefs['monitoring_topics'] = monitoring_topics
            DatabaseHelpers.update_user_preferences(user_id, current_prefs)
        
        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps({
                "message": f"Added {topic} to monitoring",
                "monitoring_topics": monitoring_topics
            })
        }
        
    except Exception as e:
        return {"statusCode": 500, "headers": get_cors_headers(), "body": json.dumps({"error": str(e)})}

def remove_monitoring_topic(event, context):
    """Remove monitoring topic"""
    try:
        user_id = extract_user_from_token(event)
        if not user_id:
            return {
                "statusCode": 401,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Unauthorized"})
            }
        
        topic = event['pathParameters']['topic']
        
        user = DatabaseHelpers.get_user_by_id(user_id)
        if not user:
            return {
                "statusCode": 404,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "User not found"})
            }
        
        current_prefs = user.get('preferences', {})
        monitoring_topics = current_prefs.get('monitoring_topics', [])
        
        if topic in monitoring_topics:
            monitoring_topics.remove(topic)
            current_prefs['monitoring_topics'] = monitoring_topics
            DatabaseHelpers.update_user_preferences(user_id, current_prefs)
        
        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps({
                "message": f"Removed {topic} from monitoring",
                "monitoring_topics": monitoring_topics
            })
        }
        
    except Exception as e:
        return {"statusCode": 500, "headers": get_cors_headers(), "body": json.dumps({"error": str(e)})}

def get_urgent_news(event, context):
    """Get urgent news"""
    try:
        # Call get_news_feed and filter for urgent
        feed_response = get_news_feed(event, context)
        if feed_response['statusCode'] == 200:
            articles = json.loads(feed_response['body'])
            urgent_articles = [a for a in articles if a.get('urgency') == 'high']
            return {
                "statusCode": 200,
                "headers": get_cors_headers(),
                "body": json.dumps(urgent_articles)
            }
        return feed_response
        
    except Exception as e:
        return {"statusCode": 500, "headers": get_cors_headers(), "body": json.dumps({"error": str(e)})}
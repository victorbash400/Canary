# utils.py - Utility functions with FIXED CORS

import jwt
import os
import requests
import json
from datetime import datetime

def get_cors_headers():
    """Get CORS headers for API responses - FIXED for production"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With,Accept,Origin,Access-Control-Request-Method,Access-Control-Request-Headers',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS,HEAD,PATCH',
        'Access-Control-Allow-Credentials': 'false',
        'Access-Control-Max-Age': '86400',
        'Content-Type': 'application/json'
    }

def extract_user_from_token(event):
    """Extract user ID from JWT token"""
    try:
        auth_header = event.get('headers', {}).get('Authorization') or event.get('headers', {}).get('authorization')
        if not auth_header:
            return None
        
        token = auth_header.replace('Bearer ', '')
        decoded = jwt.decode(token, os.environ['JWT_SECRET'], algorithms=['HS256'])
        return decoded.get('userId')
    except:
        return None

def get_unsplash_image(topic):
    """Get real image from Unsplash API for a topic"""
    try:
        # Try Unsplash API first
        unsplash_access_key = os.environ.get('UNSPLASH_ACCESS_KEY')
        if unsplash_access_key:
            url = "https://api.unsplash.com/search/photos"
            params = {
                'query': topic,
                'per_page': 1,
                'orientation': 'landscape',
                'content_filter': 'high'
            }
            headers = {'Authorization': f'Client-ID {unsplash_access_key}'}
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    image_url = data['results'][0]['urls']['regular']
                    print(f"DEBUG: Got Unsplash image for {topic}: {image_url}")
                    return image_url
        
        # Fallback to curated images if API fails
        return get_fallback_image(topic)
        
    except Exception as e:
        print(f"Unsplash error for {topic}: {e}")
        return get_fallback_image(topic)

def get_fallback_image(topic):
    """Fallback curated images for common topics"""
    topic_images = {
        "technology": "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400",
        "ai": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400",
        "artificial intelligence": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400",
        "crypto": "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=400",
        "cryptocurrency": "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=400",
        "bitcoin": "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=400",
        "tesla": "https://images.unsplash.com/photo-1560958089-b8a1929cea89?w=400",
        "apple": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400",
        "finance": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400",
        "business": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
        "ukraine": "https://images.unsplash.com/photo-1594736797933-d0d2a86e6dce?w=400",
        "war": "https://images.unsplash.com/photo-1594736797933-d0d2a86e6dce?w=400",
        "renewable energy": "https://images.unsplash.com/photo-1466611653911-95081537e5b7?w=400",
        "energy": "https://images.unsplash.com/photo-1466611653911-95081537e5b7?w=400",
        "solar": "https://images.unsplash.com/photo-1466611653911-95081537e5b7?w=400",
        "stock": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400",
        "news": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400",
        "default": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400"
    }
    
    topic_lower = topic.lower()
    for key in topic_images:
        if key in topic_lower:
            return topic_images[key]
    
    return topic_images["default"]

def analyze_article_with_gemini(article_content, topic, user_interests):
    """Analyze article with Gemini for personalization"""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return {
            "personalized_summary": "AI-curated news summary",
            "relevance_score": 75,
            "key_points": [],
            "sentiment": "neutral"
        }
    
    prompt = f"""
    You are a smart news analyst. Analyze this article about "{topic}" and create insights for someone tracking this topic.

    Article content: {article_content[:1500]}

    Create a personalized analysis with these requirements:
    - Write a PUNCHY 2-sentence summary highlighting what actually happened and why it matters
    - Extract 3-4 specific, actionable key points (not generic statements)
    - Determine if this is positive/negative/neutral news and why
    - Rate urgency: high (breaking/time-sensitive), medium (important), low (background info)
    - Score relevance 1-100 based on how significant this news is for someone tracking {topic}

    Return ONLY this JSON (no extra text):
    {{
        "personalized_summary": "Your punchy 2-sentence summary here",
        "relevance_score": 85,
        "key_points": ["Specific point 1", "Actionable insight 2", "What this means 3"],
        "sentiment": "positive/negative/neutral",
        "urgency": "high/medium/low",
        "tags": ["relevant", "topic", "tags"]
    }}

    Examples of good key_points:
    - "Tesla stock target raised to $353, indicating 9.6% upside potential"
    - "DeepSeek-VL challenges OpenAI with improved text+image reasoning"
    - "Russian forces made incremental advances near Novopavlivka"
    
    Examples of bad key_points:
    - "Latest developments in Tesla stock"
    - "AI news updates"
    - "Ukraine war continues"

    Be specific, insightful, and useful. Focus on WHAT CHANGED and WHY IT MATTERS.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            gemini_text = data['candidates'][0]['content']['parts'][0]['text']
            gemini_text = gemini_text.replace('```json', '').replace('```', '').strip()
            
            try:
                analysis = json.loads(gemini_text)
                # Ensure relevance_score is an integer
                if isinstance(analysis.get('relevance_score'), str):
                    analysis['relevance_score'] = int(analysis['relevance_score'])
                return analysis
            except Exception as parse_error:
                print(f"JSON parse error: {parse_error}")
                print(f"Raw Gemini response: {gemini_text}")
                return create_fallback_analysis(topic, article_content)
    except Exception as e:
        print(f"Gemini analysis error: {e}")
    
    return create_fallback_analysis(topic, article_content)

def create_fallback_analysis(topic, content):
    """Create a better fallback analysis"""
    # Extract first sentence for summary
    first_sentence = content.split('.')[0][:100] + "..."
    
    return {
        "personalized_summary": f"{first_sentence} This development in {topic} could impact related markets and trends.",
        "relevance_score": 75,
        "key_points": [
            f"New developments reported in {topic}",
            "Impact on related sectors and stakeholders",
            "Potential implications for future trends"
        ],
        "sentiment": "neutral",
        "urgency": "medium",
        "tags": [topic.lower().replace(' ', '_')]
    }

def format_preference_confirmation(changes_made, current_topics):
    """Format preference change confirmation message"""
    if not changes_made:
        return ""
    
    confirmation = "\n\n" + "\n".join(changes_made)
    
    if current_topics:
        confirmation += f"\n\nYour current monitoring topics: {', '.join(current_topics)}"
    
    return confirmation

def validate_topic_name(topic):
    """Validate and clean topic names"""
    if not topic or not isinstance(topic, str):
        return None
    
    # Clean the topic
    cleaned = topic.strip().title()
    
    # Minimum length check
    if len(cleaned) < 2:
        return None
    
    # Maximum length check
    if len(cleaned) > 50:
        cleaned = cleaned[:50]
    
    return cleaned

def get_user_context_summary(user_preferences, user_memory):
    """Get a summary of user context for AI responses"""
    interests = user_preferences.get('interests', [])
    monitoring = user_preferences.get('monitoring_topics', [])
    memory_snippet = user_memory.get('memorySnapshot', '') if user_memory else ''
    
    context = {
        'interests_count': len(interests),
        'monitoring_count': len(monitoring),
        'has_memory': bool(memory_snippet),
        'is_new_user': len(monitoring) == 0,
        'primary_interests': interests[:3] if interests else [],
        'recent_topics': monitoring[-3:] if monitoring else []
    }
    
    return context

def extract_entities_from_text(text):
    """Extract potential entities (companies, technologies, etc.) from text"""
    # Simple keyword extraction for common entities
    common_entities = [
        # Tech companies
        'Apple', 'Microsoft', 'Google', 'Amazon', 'Tesla', 'Meta', 'Netflix', 'Nvidia',
        # Cryptocurrencies
        'Bitcoin', 'Ethereum', 'Crypto', 'Blockchain', 'DeFi',
        # Technologies
        'AI', 'Machine Learning', 'Python', 'JavaScript', 'React', 'AWS', 'Cloud Computing',
        # Industries
        'Healthcare', 'Finance', 'Education', 'Gaming', 'E-commerce',
        # Market terms
        'Stock Market', 'IPO', 'Merger', 'Acquisition'
    ]
    
    text_upper = text.upper()
    found_entities = []
    
    for entity in common_entities:
        if entity.upper() in text_upper:
            found_entities.append(entity)
    
    return found_entities

def generate_topic_suggestions(user_interests, current_monitoring):
    """Generate topic suggestions based on user interests"""
    suggestions_map = {
        'Technology': ['AI developments', 'Cloud computing', 'Cybersecurity', 'Software engineering'],
        'Finance': ['Stock market', 'Cryptocurrency', 'Banking', 'Investment news'],
        'AI': ['Machine learning', 'OpenAI', 'Google AI', 'AI ethics'],
        'Business': ['Startups', 'Venture capital', 'IPOs', 'Market trends'],
        'Programming': ['Python updates', 'JavaScript frameworks', 'Developer tools', 'Open source']
    }
    
    suggestions = []
    for interest in user_interests:
        if interest in suggestions_map:
            for suggestion in suggestions_map[interest]:
                if suggestion not in current_monitoring and suggestion not in suggestions:
                    suggestions.append(suggestion)
    
    return suggestions[:5]  # Return top 5 suggestions
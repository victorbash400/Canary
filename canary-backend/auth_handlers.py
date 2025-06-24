# auth_handlers.py - Authentication related functions

import json
import jwt
import os
import hashlib
from datetime import datetime, timedelta
from db_helpers import DatabaseHelpers
from utils import get_cors_headers, extract_user_from_token
from email_preference_handlers import send_welcome_email

def hash_password(password):
    """Simple password hashing for hackathon"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify password against hash"""
    return hashlib.sha256(password.encode()).hexdigest() == hashed

def register_user(event, context):
    """Register a new user"""
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return {"statusCode": 200, "headers": get_cors_headers(), "body": ""}
        
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').strip().lower()
        password = body.get('password', '')
        username = body.get('username', '')
        
        if not email or not password:
            return {
                "statusCode": 400,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Email and password required"})
            }
        
        # Check if user already exists
        existing_user = DatabaseHelpers.get_user_by_email(email)
        if existing_user:
            return {
                "statusCode": 400,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "User already exists"})
            }
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        user = DatabaseHelpers.create_user(email, password_hash, username)
        
        # Send welcome email
        try:
            send_welcome_email(user['email'], user.get('username', user['email'].split('@')[0]))
        except Exception as e:
            print(f"Failed to send welcome email to {user['email']}: {e}")
            # Don't fail registration if email fails
        
        # Generate JWT token
        token = jwt.encode({
            'userId': user['userId'],
            'email': user['email'],
            'exp': datetime.utcnow() + timedelta(days=30)
        }, os.environ['JWT_SECRET'], algorithm='HS256')
        
        return {
            "statusCode": 201,
            "headers": get_cors_headers(),
            "body": json.dumps({
                "message": "User created successfully",
                "token": token,
                "user": {
                    "userId": user['userId'],
                    "email": user['email'],
                    "username": user['username']
                }
            })
        }
        
    except Exception as e:
        print(f"Registration error: {e}")
        return {
            "statusCode": 500,
            "headers": get_cors_headers(),
            "body": json.dumps({"error": "Registration failed"})
        }

def login_user(event, context):
    """Login user"""
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return {"statusCode": 200, "headers": get_cors_headers(), "body": ""}
        
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').strip().lower()
        password = body.get('password', '')
        
        if not email or not password:
            return {
                "statusCode": 400,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Email and password required"})
            }
        
        # Get user
        user = DatabaseHelpers.get_user_by_email(email)
        if not user:
            return {
                "statusCode": 401,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Invalid credentials"})
            }
        
        # Check password
        if not verify_password(password, user['passwordHash']):
            return {
                "statusCode": 401,
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Invalid credentials"})
            }
        
        # Generate JWT token
        token = jwt.encode({
            'userId': user['userId'],
            'email': user['email'],
            'exp': datetime.utcnow() + timedelta(days=30)
        }, os.environ['JWT_SECRET'], algorithm='HS256')
        
        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps({
                "message": "Login successful",
                "token": token,
                "user": {
                    "userId": user['userId'],
                    "email": user['email'],
                    "username": user['username']
                }
            })
        }
        
    except Exception as e:
        print(f"Login error: {e}")
        return {
            "statusCode": 500,
            "headers": get_cors_headers(),
            "body": json.dumps({"error": "Login failed"})
        }

def get_user_profile(event, context):
    """Get user profile"""
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
        
        # Remove sensitive data
        user_profile = {
            "userId": user['userId'],
            "email": user['email'],
            "username": user['username'],
            "preferences": user.get('preferences', {}),
            "createdAt": user['createdAt']
        }
        
        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps(user_profile)
        }
        
    except Exception as e:
        print(f"Profile error: {e}")
        return {
            "statusCode": 500,
            "headers": get_cors_headers(),
            "body": json.dumps({"error": "Failed to get profile"})
        }
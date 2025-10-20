from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import logging
from functools import wraps
from models import UserProfile, PrivacySettings, AdminAccess, SubscriptionPlan, UserSubscription
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_url_path='', static_folder='.')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})  # In production, replace * with your domain

# Root route redirects to Settings.html
@app.route('/')
def root():
    return send_from_directory('.', 'Settings.html')

# Route to serve HTML files
@app.route('/<path:filename>')
def serve_html(filename):
    if filename.endswith('.html'):
        return send_from_directory('.', filename)
    return "File not found", 404

# Route to serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://kwmpxpodmpwplujkpwjn.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3bXB4cG9kbXB3cGx1amtwd2puIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxOTMzMzMwNywiZXhwIjoyMDM0OTA5MzA3fQ.ZZM2pFJeBi3Tl6xI1NNzv3f4ETs2iIcS1EqkIowuO-M')

try:
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None  # Allow the app to start even if Supabase connection fails

def require_auth(f):
    """Decorator to check if request has valid authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        try:
            # Extract token and verify with Supabase
            token = auth_header.split(' ')[1]
            # TODO: Implement token verification with Supabase
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return jsonify({'error': 'Invalid authentication token'}), 401
    return decorated

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'database': 'connected' if supabase else 'disconnected'
    })

# User Profile API Endpoints
@app.route('/api/user/profile', methods=['GET'])
@require_auth
def get_user_profile():
    """Get the user's profile information"""
    try:
        # Get user ID from auth token
        user_id = request.headers.get('X-User-ID')  # You'll need to set this in the auth middleware
        
        if not user_id:
            return jsonify({'error': 'User ID not provided'}), 400
            
        # Query Supabase for user profile
        response = supabase.table('user_profiles').select('*').eq('id', user_id).execute()
        
        if not response.data:
            return jsonify({'error': 'User profile not found'}), 404
            
        user_profile = UserProfile.from_dict(response.data[0])
        return jsonify(user_profile.__dict__)
        
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        return jsonify({'error': 'Failed to fetch user profile'}), 500

@app.route('/api/user/profile', methods=['PUT'])
@require_auth
def update_user_profile():
    """Update the user's profile information"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({'error': 'User ID not provided'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Validate required fields
        required_fields = ['name', 'email', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Update profile in Supabase
        response = supabase.table('user_profiles').update(data).eq('id', user_id).execute()
        
        if not response.data:
            return jsonify({'error': 'Failed to update profile'}), 500
            
        updated_profile = UserProfile.from_dict(response.data[0])
        return jsonify(updated_profile.__dict__)
        
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return jsonify({'error': 'Failed to update user profile'}), 500

# Privacy Settings API Endpoints
@app.route('/api/privacy', methods=['GET'])
@require_auth
def get_privacy_settings():
    """Get the user's privacy settings"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({'error': 'User ID not provided'}), 400
            
        response = supabase.table('privacy_settings').select('*').eq('user_id', user_id).execute()
        
        # If no settings exist, create default settings
        if not response.data:
            default_settings = {
                'user_id': user_id,
                'real_time_monitoring': True,
                'data_retention': False,
                'detailed_reporting': True,
                'internal_communications': True,
                'notifications': False,
                'real_time_alerts': False
            }
            response = supabase.table('privacy_settings').insert(default_settings).execute()
            
        privacy_settings = PrivacySettings.from_dict(response.data[0])
        return jsonify(privacy_settings.__dict__)
        
    except Exception as e:
        logger.error(f"Error fetching privacy settings: {e}")
        return jsonify({'error': 'Failed to fetch privacy settings'}), 500

@app.route('/api/privacy', methods=['PUT'])
@require_auth
def update_privacy_settings():
    """Update the user's privacy settings"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({'error': 'User ID not provided'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Validate boolean fields
        boolean_fields = [
            'real_time_monitoring', 'data_retention', 'detailed_reporting',
            'internal_communications', 'notifications', 'real_time_alerts'
        ]
        
        update_data = {}
        for field in boolean_fields:
            if field in data:
                if not isinstance(data[field], bool):
                    return jsonify({'error': f'Field {field} must be a boolean'}), 400
                update_data[field] = data[field]
                
        # Update settings in Supabase
        response = supabase.table('privacy_settings').update(update_data).eq('user_id', user_id).execute()
        
        if not response.data:
            return jsonify({'error': 'Failed to update privacy settings'}), 500
            
        updated_settings = PrivacySettings.from_dict(response.data[0])
        return jsonify(updated_settings.__dict__)
        
    except Exception as e:
        logger.error(f"Error updating privacy settings: {e}")
        return jsonify({'error': 'Failed to update privacy settings'}), 500

# Admin Access API Endpoints
def require_admin(f):
    """Decorator to check if user has admin privileges"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({'error': 'User ID not provided'}), 401
            
        try:
            # Check if user has admin access
            response = supabase.table('admin_access').select('*').eq('id', user_id).execute()
            if not response.data:
                return jsonify({'error': 'Unauthorized - Admin access required'}), 403
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error checking admin access: {e}")
            return jsonify({'error': 'Failed to verify admin access'}), 500
    return decorated

@app.route('/api/admins', methods=['GET'])
@require_auth
@require_admin
def get_admin_list():
    """Get list of all admin users"""
    try:
        response = supabase.table('admin_access').select('*').execute()
        
        admin_list = [AdminAccess.from_dict(admin) for admin in response.data]
        return jsonify([admin.__dict__ for admin in admin_list])
        
    except Exception as e:
        logger.error(f"Error fetching admin list: {e}")
        return jsonify({'error': 'Failed to fetch admin list'}), 500

@app.route('/api/admins/<admin_id>', methods=['GET'])
@require_auth
@require_admin
def get_admin_details(admin_id):
    """Get details of a specific admin user"""
    try:
        response = supabase.table('admin_access').select('*').eq('id', admin_id).execute()
        
        if not response.data:
            return jsonify({'error': 'Admin not found'}), 404
            
        admin = AdminAccess.from_dict(response.data[0])
        return jsonify(admin.__dict__)
        
    except Exception as e:
        logger.error(f"Error fetching admin details: {e}")
        return jsonify({'error': 'Failed to fetch admin details'}), 500

@app.route('/api/admins', methods=['POST'])
@require_auth
@require_admin
def add_admin():
    """Add a new admin user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Validate required fields
        required_fields = ['name', 'email', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Check if email already exists
        existing = supabase.table('admin_access').select('*').eq('email', data['email']).execute()
        if existing.data:
            return jsonify({'error': 'Admin with this email already exists'}), 409
            
        # Set default permissions if not provided
        if 'permissions' not in data:
            data['permissions'] = ['read']
            
        # Insert new admin
        response = supabase.table('admin_access').insert(data).execute()
        
        new_admin = AdminAccess.from_dict(response.data[0])
        return jsonify(new_admin.__dict__), 201
        
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        return jsonify({'error': 'Failed to add admin'}), 500

@app.route('/api/admins/<admin_id>', methods=['PUT'])
@require_auth
@require_admin
def update_admin(admin_id):
    """Update an existing admin user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Check if admin exists
        existing = supabase.table('admin_access').select('*').eq('id', admin_id).execute()
        if not existing.data:
            return jsonify({'error': 'Admin not found'}), 404
            
        # If email is being updated, check for duplicates
        if 'email' in data:
            email_check = supabase.table('admin_access').select('*').eq('email', data['email']).neq('id', admin_id).execute()
            if email_check.data:
                return jsonify({'error': 'Email already in use by another admin'}), 409
                
        # Update admin
        response = supabase.table('admin_access').update(data).eq('id', admin_id).execute()
        
        updated_admin = AdminAccess.from_dict(response.data[0])
        return jsonify(updated_admin.__dict__)
        
    except Exception as e:
        logger.error(f"Error updating admin: {e}")
        return jsonify({'error': 'Failed to update admin'}), 500

@app.route('/api/admins/<admin_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_admin(admin_id):
    """Delete an admin user"""
    try:
        # Check if admin exists
        existing = supabase.table('admin_access').select('*').eq('id', admin_id).execute()
        if not existing.data:
            return jsonify({'error': 'Admin not found'}), 404
            
        # Prevent deleting the last admin
        all_admins = supabase.table('admin_access').select('*').execute()
        if len(all_admins.data) <= 1:
            return jsonify({'error': 'Cannot delete the last admin'}), 400
            
        # Delete admin
        response = supabase.table('admin_access').delete().eq('id', admin_id).execute()
        
        return jsonify({'message': 'Admin deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting admin: {e}")
        return jsonify({'error': 'Failed to delete admin'}), 500

# Subscription Management API Endpoints
@app.route('/api/subscription/plans', methods=['GET'])
@require_auth
def get_subscription_plans():
    """Get list of all available subscription plans"""
    try:
        response = supabase.table('subscription_plans').select('*').order('price').execute()
        
        plans = [SubscriptionPlan.from_dict(plan) for plan in response.data]
        return jsonify([plan.__dict__ for plan in plans])
        
    except Exception as e:
        logger.error(f"Error fetching subscription plans: {e}")
        return jsonify({'error': 'Failed to fetch subscription plans'}), 500

@app.route('/api/subscription/current', methods=['GET'])
@require_auth
def get_current_subscription():
    """Get user's current subscription"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({'error': 'User ID not provided'}), 400
            
        # Get active subscription
        response = supabase.table('user_subscriptions')\
            .select('*, subscription_plans(*)')\
            .eq('user_id', user_id)\
            .eq('status', 'active')\
            .execute()
            
        if not response.data:
            return jsonify({'error': 'No active subscription found'}), 404
            
        subscription = UserSubscription.from_dict(response.data[0])
        return jsonify(subscription.__dict__)
        
    except Exception as e:
        logger.error(f"Error fetching current subscription: {e}")
        return jsonify({'error': 'Failed to fetch current subscription'}), 500

@app.route('/api/subscription/upgrade', methods=['POST'])
@require_auth
def upgrade_subscription():
    """Upgrade user's subscription to a new plan"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({'error': 'User ID not provided'}), 400
            
        data = request.get_json()
        if not data or 'plan_id' not in data:
            return jsonify({'error': 'Plan ID not provided'}), 400
            
        # Verify plan exists
        plan_response = supabase.table('subscription_plans')\
            .select('*')\
            .eq('id', data['plan_id'])\
            .execute()
            
        if not plan_response.data:
            return jsonify({'error': 'Invalid plan ID'}), 400
            
        # Get current subscription if any
        current_sub = supabase.table('user_subscriptions')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('status', 'active')\
            .execute()
            
        # If there's an active subscription, mark it as cancelled
        if current_sub.data:
            supabase.table('user_subscriptions')\
                .update({'status': 'cancelled', 'end_date': datetime.now().isoformat()})\
                .eq('user_id', user_id)\
                .eq('status', 'active')\
                .execute()
                
        # Create new subscription
        new_subscription = {
            'user_id': user_id,
            'plan_id': data['plan_id'],
            'status': 'active',
            'start_date': datetime.now().isoformat()
        }
        
        response = supabase.table('user_subscriptions').insert(new_subscription).execute()
        
        subscription = UserSubscription.from_dict(response.data[0])
        return jsonify(subscription.__dict__), 201
        
    except Exception as e:
        logger.error(f"Error upgrading subscription: {e}")
        return jsonify({'error': 'Failed to upgrade subscription'}), 500

@app.route('/api/subscription/cancel', methods=['POST'])
@require_auth
def cancel_subscription():
    """Cancel user's current subscription"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({'error': 'User ID not provided'}), 400
            
        # Get active subscription
        current_sub = supabase.table('user_subscriptions')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('status', 'active')\
            .execute()
            
        if not current_sub.data:
            return jsonify({'error': 'No active subscription found'}), 404
            
        # Cancel subscription
        response = supabase.table('user_subscriptions')\
            .update({
                'status': 'cancelled',
                'end_date': datetime.now().isoformat()
            })\
            .eq('user_id', user_id)\
            .eq('status', 'active')\
            .execute()
            
        subscription = UserSubscription.from_dict(response.data[0])
        return jsonify(subscription.__dict__)
        
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        return jsonify({'error': 'Failed to cancel subscription'}), 500

@app.route('/api/subscription/contact', methods=['POST'])
@require_auth
def submit_contact_request():
    """Submit a contact request for custom enterprise plan"""
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({'error': 'User ID not provided'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        required_fields = ['company_name', 'contact_email', 'contact_phone', 'requirements']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Store contact request in Supabase
        contact_data = {
            'user_id': user_id,
            'company_name': data['company_name'],
            'contact_email': data['contact_email'],
            'contact_phone': data['contact_phone'],
            'requirements': data['requirements'],
            'status': 'pending'
        }
        
        response = supabase.table('enterprise_contact_requests').insert(contact_data).execute()
        
        return jsonify({
            'message': 'Contact request submitted successfully',
            'request_id': response.data[0]['id']
        }), 201
        
    except Exception as e:
        logger.error(f"Error submitting contact request: {e}")
        return jsonify({'error': 'Failed to submit contact request'}), 500

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.getenv('PORT', 5000))
    
    # Run the application
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')

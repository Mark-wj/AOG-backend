from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timedelta
from functools import wraps
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/church_website')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# Initialize extensions
CORS(app)
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Database collections
db = mongo.db

# ==================== HELPER FUNCTIONS ====================

def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return None
    doc['_id'] = str(doc['_id'])
    if 'createdAt' in doc and isinstance(doc['createdAt'], datetime):
        doc['createdAt'] = doc['createdAt'].isoformat()
    if 'updatedAt' in doc and isinstance(doc['updatedAt'], datetime):
        doc['updatedAt'] = doc['updatedAt'].isoformat()
    if 'uploadedAt' in doc and isinstance(doc['uploadedAt'], datetime):
        doc['uploadedAt'] = doc['uploadedAt'].isoformat()
    if 'subscribedAt' in doc and isinstance(doc['subscribedAt'], datetime):
        doc['subscribedAt'] = doc['subscribedAt'].isoformat()
    return doc

def serialize_docs(docs):
    """Convert list of MongoDB documents to JSON-serializable format"""
    return [serialize_doc(doc) for doc in docs]

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error'}), 500

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/api/admin/register', methods=['POST'])
def register_admin():
    """Register new admin user (should be protected in production)"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Missing required fields'}), 400
        
        # Check if admin already exists
        existing_admin = db.admins.find_one({
            '$or': [
                {'username': data['username']},
                {'email': data['email']}
            ]
        })
        
        if existing_admin:
            return jsonify({'message': 'Admin already exists'}), 400
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        # Create admin
        admin_data = {
            'username': data['username'],
            'email': data['email'],
            'password': hashed_password,
            'role': data.get('role', 'admin'),
            'createdAt': datetime.utcnow()
        }
        
        result = db.admins.insert_one(admin_data)
        
        return jsonify({
            'message': 'Admin created successfully',
            'id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/admin/login', methods=['POST'])
def login_admin():
    """Admin login endpoint"""
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Missing credentials'}), 400
        
        # Find admin
        admin = db.admins.find_one({'username': data['username']})
        
        if not admin:
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Verify password
        if not bcrypt.check_password_hash(admin['password'], data['password']):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Create access token
        access_token = create_access_token(
            identity=str(admin['_id']),
            additional_claims={
                'username': admin['username'],
                'role': admin['role']
            }
        )
        
        return jsonify({
            'token': access_token,
            'admin': {
                'id': str(admin['_id']),
                'username': admin['username'],
                'email': admin['email'],
                'role': admin['role']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ==================== EVENT ROUTES ====================

@app.route('/api/events', methods=['GET'])
def get_events():
    """Get all events or filter by category"""
    try:
        category = request.args.get('category')
        query = {'category': category} if category else {}
        
        events = db.events.find(query).sort('date', -1)
        return jsonify(serialize_docs(events)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/events/<event_id>', methods=['GET'])
def get_event(event_id):
    """Get single event by ID"""
    try:
        event = db.events.find_one({'_id': ObjectId(event_id)})
        
        if not event:
            return jsonify({'message': 'Event not found'}), 404
        
        return jsonify(serialize_doc(event)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/events', methods=['POST'])
@jwt_required()
def create_event():
    """Create new event (protected)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'date', 'time', 'location', 'description', 'image']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        # Create event document
        event_data = {
            'title': data['title'],
            'date': data['date'],
            'time': data['time'],
            'location': data['location'],
            'description': data['description'],
            'image': data['image'],
            'category': data.get('category', 'upcoming'),
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        
        result = db.events.insert_one(event_data)
        event_data['_id'] = str(result.inserted_id)
        
        return jsonify(serialize_doc(event_data)), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/events/<event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    """Update event (protected)"""
    try:
        data = request.get_json()
        data['updatedAt'] = datetime.utcnow()
        
        result = db.events.update_one(
            {'_id': ObjectId(event_id)},
            {'$set': data}
        )
        
        if result.matched_count == 0:
            return jsonify({'message': 'Event not found'}), 404
        
        updated_event = db.events.find_one({'_id': ObjectId(event_id)})
        return jsonify(serialize_doc(updated_event)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/events/<event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    """Delete event (protected)"""
    try:
        result = db.events.delete_one({'_id': ObjectId(event_id)})
        
        if result.deleted_count == 0:
            return jsonify({'message': 'Event not found'}), 404
        
        return jsonify({'message': 'Event deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ==================== SERMON ROUTES ====================

@app.route('/api/sermons', methods=['GET'])
def get_sermons():
    """Get all sermons"""
    try:
        sermons = db.sermons.find().sort('date', -1)
        return jsonify(serialize_docs(sermons)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/sermons/<sermon_id>', methods=['GET'])
def get_sermon(sermon_id):
    """Get single sermon and increment view count"""
    try:
        sermon = db.sermons.find_one({'_id': ObjectId(sermon_id)})
        
        if not sermon:
            return jsonify({'message': 'Sermon not found'}), 404
        
        # Increment view count
        db.sermons.update_one(
            {'_id': ObjectId(sermon_id)},
            {'$inc': {'views': 1}}
        )
        
        sermon['views'] = sermon.get('views', 0) + 1
        
        return jsonify(serialize_doc(sermon)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/sermons', methods=['POST'])
@jwt_required()
def create_sermon():
    """Create new sermon (protected)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'speaker', 'date', 'description', 'image']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        # Create sermon document
        sermon_data = {
            'title': data['title'],
            'speaker': data['speaker'],
            'date': data['date'],
            'series': data.get('series', ''),
            'description': data['description'],
            'image': data['image'],
            'videoUrl': data.get('videoUrl', ''),
            'audioUrl': data.get('audioUrl', ''),
            'views': 0,
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        
        result = db.sermons.insert_one(sermon_data)
        sermon_data['_id'] = str(result.inserted_id)
        
        return jsonify(serialize_doc(sermon_data)), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/sermons/<sermon_id>', methods=['PUT'])
@jwt_required()
def update_sermon(sermon_id):
    """Update sermon (protected)"""
    try:
        data = request.get_json()
        data['updatedAt'] = datetime.utcnow()
        
        result = db.sermons.update_one(
            {'_id': ObjectId(sermon_id)},
            {'$set': data}
        )
        
        if result.matched_count == 0:
            return jsonify({'message': 'Sermon not found'}), 404
        
        updated_sermon = db.sermons.find_one({'_id': ObjectId(sermon_id)})
        return jsonify(serialize_doc(updated_sermon)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/sermons/<sermon_id>', methods=['DELETE'])
@jwt_required()
def delete_sermon(sermon_id):
    """Delete sermon (protected)"""
    try:
        result = db.sermons.delete_one({'_id': ObjectId(sermon_id)})
        
        if result.deleted_count == 0:
            return jsonify({'message': 'Sermon not found'}), 404
        
        return jsonify({'message': 'Sermon deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ==================== GALLERY ROUTES ====================

@app.route('/api/gallery', methods=['GET'])
def get_gallery():
    """Get all gallery images or filter by category"""
    try:
        category = request.args.get('category')
        query = {'category': category} if category else {}
        
        images = db.gallery.find(query).sort('uploadedAt', -1)
        return jsonify(serialize_docs(images)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/gallery', methods=['POST'])
@jwt_required()
def create_gallery_image():
    """Add new image to gallery (protected)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title') or not data.get('imageUrl'):
            return jsonify({'message': 'Missing required fields'}), 400
        
        # Create gallery document
        gallery_data = {
            'title': data['title'],
            'description': data.get('description', ''),
            'imageUrl': data['imageUrl'],
            'category': data.get('category', 'general'),
            'uploadedAt': datetime.utcnow()
        }
        
        result = db.gallery.insert_one(gallery_data)
        gallery_data['_id'] = str(result.inserted_id)
        
        return jsonify(serialize_doc(gallery_data)), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/gallery/<image_id>', methods=['DELETE'])
@jwt_required()
def delete_gallery_image(image_id):
    """Delete gallery image (protected)"""
    try:
        result = db.gallery.delete_one({'_id': ObjectId(image_id)})
        
        if result.deleted_count == 0:
            return jsonify({'message': 'Image not found'}), 404
        
        return jsonify({'message': 'Image deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ==================== MESSAGE ROUTES ====================

@app.route('/api/messages', methods=['POST'])
def submit_message():
    """Submit contact message (public)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'subject', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        # Create message document
        message_data = {
            'name': data['name'],
            'email': data['email'],
            'subject': data['subject'],
            'message': data['message'],
            'status': 'new',
            'createdAt': datetime.utcnow()
        }
        
        result = db.messages.insert_one(message_data)
        
        return jsonify({
            'message': 'Message sent successfully',
            'id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/messages', methods=['GET'])
@jwt_required()
def get_messages():
    """Get all messages (protected)"""
    try:
        messages = db.messages.find().sort('createdAt', -1)
        return jsonify(serialize_docs(messages)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/messages/<message_id>', methods=['PATCH'])
@jwt_required()
def update_message_status(message_id):
    """Update message status (protected)"""
    try:
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({'message': 'Status field required'}), 400
        
        result = db.messages.update_one(
            {'_id': ObjectId(message_id)},
            {'$set': {'status': data['status']}}
        )
        
        if result.matched_count == 0:
            return jsonify({'message': 'Message not found'}), 404
        
        updated_message = db.messages.find_one({'_id': ObjectId(message_id)})
        return jsonify(serialize_doc(updated_message)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/messages/<message_id>', methods=['DELETE'])
@jwt_required()
def delete_message(message_id):
    """Delete message (protected)"""
    try:
        result = db.messages.delete_one({'_id': ObjectId(message_id)})
        
        if result.deleted_count == 0:
            return jsonify({'message': 'Message not found'}), 404
        
        return jsonify({'message': 'Message deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ==================== NEWSLETTER ROUTES ====================

@app.route('/api/subscribe', methods=['POST'])
def subscribe_newsletter():
    """Subscribe to newsletter (public)"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({'message': 'Email required'}), 400
        
        # Check if already subscribed
        existing = db.subscribers.find_one({'email': data['email']})
        
        if existing:
            if existing.get('active', True):
                return jsonify({'message': 'Already subscribed'}), 400
            else:
                # Reactivate subscription
                db.subscribers.update_one(
                    {'email': data['email']},
                    {'$set': {'active': True}}
                )
                return jsonify({'message': 'Resubscribed successfully'}), 200
        
        # Create new subscriber
        subscriber_data = {
            'email': data['email'],
            'subscribedAt': datetime.utcnow(),
            'active': True
        }
        
        db.subscribers.insert_one(subscriber_data)
        
        return jsonify({'message': 'Subscribed successfully'}), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/subscribers', methods=['GET'])
@jwt_required()
def get_subscribers():
    """Get all active subscribers (protected)"""
    try:
        subscribers = db.subscribers.find({'active': True}).sort('subscribedAt', -1)
        return jsonify(serialize_docs(subscribers)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ==================== ADMIN STATS ====================

@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
def get_admin_stats():
    """Get dashboard statistics (protected)"""
    try:
        stats = {
            'totalEvents': db.events.count_documents({}),
            'totalSermons': db.sermons.count_documents({}),
            'totalMessages': db.messages.count_documents({'status': 'new'}),
            'totalGalleryImages': db.gallery.count_documents({}),
            'totalSubscribers': db.subscribers.count_documents({'active': True})
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.command('ping')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# ==================== ROOT ENDPOINT ====================

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'Armor of God Church API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'auth': '/api/admin/login',
            'events': '/api/events',
            'sermons': '/api/sermons',
            'gallery': '/api/gallery',
            'messages': '/api/messages',
            'subscribe': '/api/subscribe',
            'health': '/api/health'
        }
    }), 200
@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get site settings - Public endpoint for music URL"""
    try:
        settings = db.settings.find_one({'type': 'site'})
        
        if not settings:
            # Return default settings if none exist
            return jsonify({
                'musicUrl': '',
                'musicEnabled': False
            }), 200
        
        # Return only public settings
        return jsonify({
            'musicUrl': settings.get('musicUrl', ''),
            'musicEnabled': settings.get('musicEnabled', False)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/settings/music', methods=['GET'])
def get_music_settings():
    """Get music settings only - Public endpoint"""
    try:
        settings = db.settings.find_one({'type': 'site'})
        
        if not settings or not settings.get('musicEnabled', False):
            return jsonify({'musicUrl': ''}), 200
        
        return jsonify({
            'musicUrl': settings.get('musicUrl', '')
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/settings', methods=['PUT'])
@jwt_required()
def update_settings():
    """Update site settings - Protected admin endpoint"""
    try:
        data = request.get_json()
        
        settings_data = {
            'type': 'site',
            'musicUrl': data.get('musicUrl', ''),
            'musicEnabled': data.get('musicEnabled', False),
            'updatedAt': datetime.utcnow()
        }
        
        # Upsert settings (update if exists, create if not)
        result = db.settings.update_one(
            {'type': 'site'},
            {'$set': settings_data},
            upsert=True
        )
        
        return jsonify({
            'message': 'Settings updated successfully',
            'settings': settings_data
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500


# ==================== RUN SERVER ====================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
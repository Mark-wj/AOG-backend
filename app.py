from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ==================== CONFIGURATION ====================
# Explicitly load environment variables with fallbacks
MONGO_URI = os.environ.get('MONGO_URI') or os.getenv('MONGO_URI')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or os.getenv('JWT_SECRET_KEY') or 'default-jwt-secret-change-me'
FLASK_ENV = os.environ.get('FLASK_ENV') or os.getenv('FLASK_ENV', 'development')

# Log configuration (helps debug Railway issues)
print(f"🔧 Environment: {FLASK_ENV}")
print(f"🔧 MONGO_URI configured: {bool(MONGO_URI)}")
print(f"🔧 JWT_SECRET_KEY configured: {bool(JWT_SECRET_KEY)}")

if not MONGO_URI:
    print("⚠️  WARNING: MONGO_URI not set! Database will not work.")
    
app.config['MONGO_URI'] = MONGO_URI
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# ==================== CRITICAL: CORS CONFIGURATION ====================
# Allow your production domain and localhost for testing
CORS(app, 
     resources={r"/*": {
         "origins": [
             "https://www.armorofgod.digital",
             "https://armorofgod.digital",
             "http://localhost:5173",
             "http://localhost:3000"
         ]
     }},
     methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=True,
     expose_headers=['Content-Type', 'Authorization']
)

# ==================== INITIALIZE EXTENSIONS ====================
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# ==================== HELPER FUNCTIONS ====================

def get_db():
    """Safely get database connection"""
    if mongo and mongo.db:
        return mongo.db
    return None

def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(d) for d in doc]
    if isinstance(doc, dict):
        serialized = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = serialize_doc(value)
            elif isinstance(value, list):
                serialized[key] = [serialize_doc(item) if isinstance(item, dict) else item for item in value]
            else:
                serialized[key] = value
        return serialized
    return doc

# ==================== ROOT ROUTE ====================

@app.route('/', methods=['GET'])
def index():
    """API root endpoint"""
    return jsonify({
        'message': 'Armor of God Church API',
        'version': '1.0.0',
        'status': 'active',
        'endpoints': {
            'health': '/api/health',
            'events': '/api/events',
            'sermons': '/api/sermons',
            'gallery': '/api/gallery',
            'messages': '/api/messages',
            'settings': '/api/settings',
            'admin': '/api/admin/*'
        }
    }), 200

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with improved error handling"""
    try:
        # Check if MONGO_URI is configured
        if not app.config.get('MONGO_URI'):
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': 'MONGO_URI not configured',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # Check if mongo instance exists
        if not mongo:
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': 'MongoDB instance not initialized',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # Check if database connection is available
        db = get_db()
        if db is None:
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': 'Database connection is None - check MONGO_URI',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # Try to ping the database
        db.command('ping')
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/api/admin/register', methods=['POST'])
def register_admin():
    """Register new admin user"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        data = request.get_json()
        
        # Check if admin already exists
        existing_admin = db.admins.find_one({'username': data['username']})
        if existing_admin:
            return jsonify({'message': 'Admin already exists'}), 400
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        # Create admin
        admin_data = {
            'username': data['username'],
            'email': data['email'],
            'password': hashed_password,
            'createdAt': datetime.utcnow()
        }
        
        result = db.admins.insert_one(admin_data)
        
        return jsonify({
            'message': 'Admin created successfully',
            'adminId': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/admin/login', methods=['POST'])
def login_admin():
    """Admin login"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        data = request.get_json()
        
        # Find admin
        admin = db.admins.find_one({'username': data['username']})
        
        if not admin or not bcrypt.check_password_hash(admin['password'], data['password']):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Create access token
        access_token = create_access_token(identity=str(admin['_id']))
        
        return jsonify({
            'token': access_token,
            'admin': {
                'id': str(admin['_id']),
                'username': admin['username'],
                'email': admin['email']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ==================== EVENTS ROUTES ====================

@app.route('/api/events', methods=['GET'])
def get_events():
    """Get all events, optionally filtered by category"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        category = request.args.get('category')
        query = {'category': category} if category else {}
        
        events = list(db.events.find(query).sort('date', -1))
        return jsonify(serialize_doc(events)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/events/<event_id>', methods=['GET'])
def get_event(event_id):
    """Get single event by ID"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
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
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        data = request.get_json()
        
        event_data = {
            'title': data['title'],
            'date': data['date'],
            'time': data['time'],
            'location': data['location'],
            'description': data['description'],
            'image': data.get('image', ''),
            'category': data.get('category', 'upcoming'),
            'createdAt': datetime.utcnow()
        }
        
        result = db.events.insert_one(event_data)
        
        return jsonify({
            'message': 'Event created successfully',
            'eventId': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/events/<event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    """Update event (protected)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        data = request.get_json()
        
        update_data = {
            'title': data['title'],
            'date': data['date'],
            'time': data['time'],
            'location': data['location'],
            'description': data['description'],
            'image': data.get('image', ''),
            'category': data.get('category', 'upcoming'),
            'updatedAt': datetime.utcnow()
        }
        
        result = db.events.update_one(
            {'_id': ObjectId(event_id)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'message': 'Event not found'}), 404
        
        return jsonify({'message': 'Event updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/events/<event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    """Delete event (protected)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        result = db.events.delete_one({'_id': ObjectId(event_id)})
        
        if result.deleted_count == 0:
            return jsonify({'message': 'Event not found'}), 404
        
        return jsonify({'message': 'Event deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ==================== SERMONS ROUTES ====================

@app.route('/api/sermons', methods=['GET'])
def get_sermons():
    """Get all sermons"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        sermons = list(db.sermons.find().sort('date', -1))
        return jsonify(serialize_doc(sermons)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/sermons/<sermon_id>', methods=['GET'])
def get_sermon(sermon_id):
    """Get single sermon and increment view count"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
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
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        data = request.get_json()
        
        sermon_data = {
            'title': data['title'],
            'speaker': data['speaker'],
            'date': data['date'],
            'series': data.get('series', ''),
            'description': data['description'],
            'thumbnail': data.get('thumbnail', ''),
            'videoUrl': data.get('videoUrl', ''),
            'audioUrl': data.get('audioUrl', ''),
            'views': 0,
            'createdAt': datetime.utcnow()
        }
        
        result = db.sermons.insert_one(sermon_data)
        
        return jsonify({
            'message': 'Sermon created successfully',
            'sermonId': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/sermons/<sermon_id>', methods=['PUT'])
@jwt_required()
def update_sermon(sermon_id):
    """Update sermon (protected)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        data = request.get_json()
        
        update_data = {
            'title': data['title'],
            'speaker': data['speaker'],
            'date': data['date'],
            'series': data.get('series', ''),
            'description': data['description'],
            'thumbnail': data.get('thumbnail', ''),
            'videoUrl': data.get('videoUrl', ''),
            'audioUrl': data.get('audioUrl', ''),
            'updatedAt': datetime.utcnow()
        }
        
        result = db.sermons.update_one(
            {'_id': ObjectId(sermon_id)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'message': 'Sermon not found'}), 404
        
        return jsonify({'message': 'Sermon updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/sermons/<sermon_id>', methods=['DELETE'])
@jwt_required()
def delete_sermon(sermon_id):
    """Delete sermon (protected)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        result = db.sermons.delete_one({'_id': ObjectId(sermon_id)})
        
        if result.deleted_count == 0:
            return jsonify({'message': 'Sermon not found'}), 404
        
        return jsonify({'message': 'Sermon deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ==================== GALLERY ROUTES ====================

@app.route('/api/gallery', methods=['GET'])
def get_gallery():
    """Get all gallery images, optionally filtered by category"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        category = request.args.get('category')
        query = {'category': category} if category else {}
        
        images = list(db.gallery.find(query).sort('createdAt', -1))
        return jsonify(serialize_doc(images)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/gallery', methods=['POST'])
@jwt_required()
def create_gallery_image():
    """Upload gallery image (protected)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        data = request.get_json()
        
        image_data = {
            'title': data['title'],
            'category': data['category'],
            'imageUrl': data['imageUrl'],
            'description': data.get('description', ''),
            'createdAt': datetime.utcnow()
        }
        
        result = db.gallery.insert_one(image_data)
        
        return jsonify({
            'message': 'Image added successfully',
            'imageId': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/gallery/<image_id>', methods=['DELETE'])
@jwt_required()
def delete_gallery_image(image_id):
    """Delete gallery image (protected)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        result = db.gallery.delete_one({'_id': ObjectId(image_id)})
        
        if result.deleted_count == 0:
            return jsonify({'message': 'Image not found'}), 404
        
        return jsonify({'message': 'Image deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ==================== MESSAGES ROUTES ====================

@app.route('/api/messages', methods=['POST'])
def submit_message():
    """Submit contact form message (public)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        data = request.get_json()
        
        message_data = {
            'name': data['name'],
            'email': data['email'],
            'subject': data.get('subject', ''),
            'message': data['message'],
            'status': 'new',
            'createdAt': datetime.utcnow()
        }
        
        result = db.messages.insert_one(message_data)
        
        return jsonify({
            'message': 'Message sent successfully',
            'messageId': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/messages', methods=['GET'])
@jwt_required()
def get_messages():
    """Get all messages (protected)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        messages = list(db.messages.find().sort('createdAt', -1))
        return jsonify(serialize_doc(messages)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/messages/<message_id>', methods=['PATCH'])
@jwt_required()
def update_message_status(message_id):
    """Update message status (protected)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        data = request.get_json()
        
        result = db.messages.update_one(
            {'_id': ObjectId(message_id)},
            {'$set': {'status': data['status'], 'updatedAt': datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            return jsonify({'message': 'Message not found'}), 404
        
        return jsonify({'message': 'Status updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/messages/<message_id>', methods=['DELETE'])
@jwt_required()
def delete_message(message_id):
    """Delete message (protected)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
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
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        data = request.get_json()
        
        # Check if already subscribed
        existing = db.subscribers.find_one({'email': data['email']})
        if existing:
            return jsonify({'message': 'Already subscribed'}), 400
        
        subscriber_data = {
            'email': data['email'],
            'status': 'active',
            'subscribedAt': datetime.utcnow()
        }
        
        result = db.subscribers.insert_one(subscriber_data)
        
        return jsonify({
            'message': 'Subscribed successfully',
            'subscriberId': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/subscribers', methods=['GET'])
@jwt_required()
def get_subscribers():
    """Get all subscribers (protected)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        subscribers = list(db.subscribers.find({'status': 'active'}))
        return jsonify(serialize_doc(subscribers)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ==================== SETTINGS ROUTES ====================

@app.route('/api/settings', methods=['GET'])
@app.route('/settings', methods=['GET'])  # Compatibility route
def get_settings():
    """Get site settings (public endpoint for music URL)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        settings = db.settings.find_one({'type': 'site'})
        
        if not settings:
            return jsonify({
                'musicUrl': '',
                'musicEnabled': False
            }), 200
        
        return jsonify({
            'musicUrl': settings.get('musicUrl', ''),
            'musicEnabled': settings.get('musicEnabled', False)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/settings/music', methods=['GET'])
@app.route('/settings/music', methods=['GET'])  # Compatibility route
def get_music_settings():
    """Get music settings only (public endpoint)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
        
        settings = db.settings.find_one({'type': 'site'})
        
        # ✅ explicit None check
        if settings is None or not settings.get('musicEnabled', False):
            return jsonify({'musicUrl': ''}), 200
        
        return jsonify({
            'musicUrl': settings.get('musicUrl', '')
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500


@app.route('/api/settings', methods=['PUT'])
@jwt_required()
def update_settings():
    """Update site settings (protected)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        data = request.get_json()
        
        settings_data = {
            'type': 'site',
            'musicUrl': data.get('musicUrl', ''),
            'musicEnabled': data.get('musicEnabled', False),
            'updatedAt': datetime.utcnow()
        }
        
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

# ==================== ADMIN STATS ====================

@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
def get_admin_stats():
    """Get dashboard statistics (protected)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'message': 'Database not available'}), 503
            
        stats = {
            'totalEvents': db.events.count_documents({}),
            'totalSermons': db.sermons.count_documents({}),
            'totalMessages': db.messages.count_documents({}),
            'newMessages': db.messages.count_documents({'status': 'new'}),
            'totalGalleryImages': db.gallery.count_documents({}),
            'totalSubscribers': db.subscribers.count_documents({'status': 'active'})
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ==================== RUN APP ====================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')
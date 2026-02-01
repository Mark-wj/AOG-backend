from app import app
import os

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print("=" * 60)
    print("🚀 Starting Armor of God Church API Server")
    print("=" * 60)
    print(f"📡 Server running on: http://localhost:{port}")
    print(f"🔧 Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"🗄️  Database: {os.getenv('MONGO_URI', 'mongodb://localhost:27017/church_website')}")
    print("=" * 60)
    print("\n✨ API Endpoints:")
    print("   - GET  /                      - API Info")
    print("   - GET  /api/health            - Health Check")
    print("   - POST /api/admin/login       - Admin Login")
    print("   - GET  /api/events            - Get Events")
    print("   - GET  /api/sermons           - Get Sermons")
    print("   - GET  /api/gallery           - Get Gallery")
    print("   - POST /api/messages          - Submit Message")
    print("   - POST /api/subscribe         - Subscribe Newsletter")
    print("\n🔐 Protected Endpoints (require JWT token):")
    print("   - POST /api/events            - Create Event")
    print("   - PUT  /api/events/:id        - Update Event")
    print("   - DEL  /api/events/:id        - Delete Event")
    print("   - (Similar for sermons, gallery, messages)")
    print("\n✅ Server is ready! Press Ctrl+C to stop.\n")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
# seed_database.py - Database seeder for Church Website (FIXED)
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Bcrypt (same as Flask app)
bcrypt = Bcrypt()

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/church_website')
client = MongoClient(MONGO_URI)
db = client.get_database()

print("🌱 Starting database seed...")

# ==================== CLEAR EXISTING DATA ====================

print("🗑️  Clearing existing data...")
db.events.delete_many({})
db.sermons.delete_many({})
db.gallery.delete_many({})
db.messages.delete_many({})
db.admins.delete_many({})
db.subscribers.delete_many({})

# ==================== SAMPLE DATA ====================

# Events
sample_events = [
    {
        'title': 'Sunday Worship Service',
        'date': '2025-02-02',
        'time': '10:30 AM',
        'location': 'Main Sanctuary',
        'description': 'Join us for a powerful worship experience as we praise and glorify God together.',
        'image': 'https://images.unsplash.com/photo-1438232992991-995b7058bbb3?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
        'category': 'upcoming',
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow()
    },
    {
        'title': 'Youth Night',
        'date': '2025-02-07',
        'time': '7:00 PM',
        'location': 'Youth Center',
        'description': 'Dynamic worship and teaching designed specifically for teenagers and young adults.',
        'image': 'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
        'category': 'upcoming',
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow()
    },
    {
        'title': 'Bible Study Wednesday',
        'date': '2025-02-05',
        'time': '7:00 PM',
        'location': 'Fellowship Hall',
        'description': 'Deep dive into God\'s Word with interactive discussion and practical application.',
        'image': 'https://images.unsplash.com/photo-1481277542470-605612bd2d61?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
        'category': 'upcoming',
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow()
    },
    {
        'title': 'Community Outreach',
        'date': '2025-02-09',
        'time': '9:00 AM',
        'location': 'City Center',
        'description': 'Serving our community and sharing God\'s love through action.',
        'image': 'https://images.unsplash.com/photo-1522543558187-768b6df7c25c?w=400&auto=format&fit=crop&q=60',
        'category': 'upcoming',
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow()
    },
    {
        'title': 'Fall Harvest Festival',
        'date': '2024-10-31',
        'time': '4:00 PM',
        'location': 'Church Grounds',
        'description': 'A wonderful community event with games, food, and fellowship for all ages.',
        'image': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
        'category': 'past',
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow()
    }
]

# Sermons
sample_sermons = [
    {
        'title': 'The Power of Faith',
        'speaker': 'Pastor Gary Morgan',
        'date': 'January 26, 2025',
        'series': 'Foundations of Faith',
        'description': 'Exploring the transformative power of faith in our daily lives and how it shapes our relationship with God.',
        'image': 'https://images.unsplash.com/photo-1501281667305-0d4ebd5b1e67?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
        'videoUrl': 'https://youtube.com/watch?v=example1',
        'audioUrl': '',
        'views': 145,
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow()
    },
    {
        'title': 'Walking in Grace',
        'speaker': 'Pastor Gary Morgan',
        'date': 'January 19, 2025',
        'series': 'Grace Journey',
        'description': 'Understanding God\'s grace and how to walk in it every day of our lives.',
        'image': 'https://images.unsplash.com/photo-1438032005730-c779502df39b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
        'videoUrl': 'https://youtube.com/watch?v=example2',
        'audioUrl': '',
        'views': 198,
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow()
    },
    {
        'title': 'Hope in Hard Times',
        'speaker': 'Pastor Gary Morgan',
        'date': 'January 12, 2025',
        'series': 'Endurance Series',
        'description': 'Finding hope and strength through difficult seasons by anchoring ourselves in Christ.',
        'image': 'https://images.unsplash.com/photo-1465847899084-d164dfdded4a?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
        'videoUrl': 'https://youtube.com/watch?v=example3',
        'audioUrl': '',
        'views': 223,
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow()
    },
    {
        'title': 'The Joy of Giving',
        'speaker': 'Pastor Gary Morgan',
        'date': 'January 5, 2025',
        'series': 'Generous Life',
        'description': 'Discovering the biblical principles of generosity and the blessing of giving.',
        'image': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
        'videoUrl': 'https://youtube.com/watch?v=example4',
        'audioUrl': '',
        'views': 176,
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow()
    },
    {
        'title': 'Armor of God',
        'speaker': 'Pastor Gary Morgan',
        'date': 'December 29, 2024',
        'series': 'Spiritual Warfare',
        'description': 'Understanding and putting on the full armor of God to stand against spiritual attacks.',
        'image': 'https://images.unsplash.com/photo-1519491050282-cf00c82424b4?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
        'videoUrl': 'https://youtube.com/watch?v=example5',
        'audioUrl': '',
        'views': 267,
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow()
    },
    {
        'title': 'Living in the End Times',
        'speaker': 'Pastor Gary Morgan',
        'date': 'December 22, 2024',
        'series': 'Prophecy & Preparedness',
        'description': 'Understanding the signs of the times and preparing for Christ\'s soon return.',
        'image': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
        'videoUrl': 'https://youtube.com/watch?v=example6',
        'audioUrl': '',
        'views': 312,
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow()
    }
]

# Gallery
sample_gallery = [
    {
        'title': 'Sunday Worship',
        'description': 'Praising God together in the Main Sanctuary',
        'imageUrl': 'https://images.unsplash.com/photo-1438232992991-995b7058bbb3?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
        'category': 'worship',
        'uploadedAt': datetime.utcnow()
    },
    {
        'title': 'Baptism Service',
        'description': 'Celebrating new believers in Christ',
        'imageUrl': 'https://images.unsplash.com/photo-1724035292068-f9e0b3ddd2b7?q=80&w=1169&auto=format&fit=crop',
        'category': 'baptism',
        'uploadedAt': datetime.utcnow()
    },
    {
        'title': 'Community Outreach',
        'description': 'Serving our neighborhood with love',
        'imageUrl': 'https://images.unsplash.com/photo-1522543558187-768b6df7c25c?w=400&auto=format&fit=crop&q=60',
        'category': 'outreach',
        'uploadedAt': datetime.utcnow()
    },
    {
        'title': 'Christmas Eve Service',
        'description': 'Celebrating the birth of our Savior',
        'imageUrl': 'https://images.unsplash.com/photo-1702399853315-dd6344d1c1e9?q=80&w=687&auto=format&fit=crop',
        'category': 'special',
        'uploadedAt': datetime.utcnow()
    },
    {
        'title': 'Youth Ministry',
        'description': 'Empowering the next generation',
        'imageUrl': 'https://images.unsplash.com/photo-1593896385987-16bcbf9451e5?q=80&w=997&auto=format&fit=crop',
        'category': 'youth',
        'uploadedAt': datetime.utcnow()
    },
    {
        'title': 'Prayer Night',
        'description': 'Interceding for our community and world',
        'imageUrl': 'https://images.unsplash.com/photo-1641337261712-3cb3f398331f?q=80&w=687&auto=format&fit=crop',
        'category': 'prayer',
        'uploadedAt': datetime.utcnow()
    },
    {
        'title': 'Church Building',
        'description': 'Our beautiful sanctuary where we gather',
        'imageUrl': 'https://images.unsplash.com/photo-1519491050282-cf00c82424b4?q=80&w=1170&auto=format&fit=crop',
        'category': 'building',
        'uploadedAt': datetime.utcnow()
    },
    {
        'title': 'Bible Study',
        'description': 'Growing deeper in God\'s Word together',
        'imageUrl': 'https://images.unsplash.com/photo-1481277542470-605612bd2d61?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
        'category': 'study',
        'uploadedAt': datetime.utcnow()
    }
]

# Sample messages (for testing)
sample_messages = [
    {
        'name': 'John Smith',
        'email': 'john@example.com',
        'subject': 'Interested in joining the choir',
        'message': 'I would love to join the worship team. I have been singing for 10 years.',
        'status': 'new',
        'createdAt': datetime.utcnow()
    },
    {
        'name': 'Sarah Johnson',
        'email': 'sarah@example.com',
        'subject': 'Question about youth program',
        'message': 'What age groups are included in the youth ministry?',
        'status': 'new',
        'createdAt': datetime.utcnow()
    }
]

# ==================== INSERT DATA ====================

print("✅ Inserting events...")
db.events.insert_many(sample_events)

print("✅ Inserting sermons...")
db.sermons.insert_many(sample_sermons)

print("✅ Inserting gallery images...")
db.gallery.insert_many(sample_gallery)

print("✅ Inserting sample messages...")
db.messages.insert_many(sample_messages)

# Create admin user with CORRECT Flask-Bcrypt format
print("✅ Creating admin user...")

# IMPORTANT: Use Flask-Bcrypt's generate_password_hash method
# This returns bytes, so we decode to string for MongoDB
hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')

admin_user = {
    'username': 'admin',
    'email': 'admin@armorofgod.org',
    'password': hashed_password,  # Correctly hashed with Flask-Bcrypt
    'role': 'superadmin',
    'createdAt': datetime.utcnow()
}

db.admins.insert_one(admin_user)

# ==================== CREATE INDEXES ====================

print("📊 Creating database indexes...")

# Events indexes
db.events.create_index([('category', 1)])
db.events.create_index([('date', -1)])

# Sermons indexes
db.sermons.create_index([('date', -1)])
db.sermons.create_index([('speaker', 1)])
db.sermons.create_index([('series', 1)])

# Gallery indexes
db.gallery.create_index([('category', 1)])
db.gallery.create_index([('uploadedAt', -1)])

# Messages indexes
db.messages.create_index([('status', 1)])
db.messages.create_index([('createdAt', -1)])

# Admin indexes
db.admins.create_index([('username', 1)], unique=True)
db.admins.create_index([('email', 1)], unique=True)

# Subscribers indexes
db.subscribers.create_index([('email', 1)], unique=True)

# ==================== SUMMARY ====================

print("\n🎉 Database seeding completed successfully!")
print("\n📋 Summary:")
print(f"   - Events: {len(sample_events)}")
print(f"   - Sermons: {len(sample_sermons)}")
print(f"   - Gallery Images: {len(sample_gallery)}")
print(f"   - Messages: {len(sample_messages)}")
print(f"   - Admin Users: 1")

print("\n🔐 Admin Credentials:")
print("   Username: admin")
print("   Password: admin123")
print("   Email: admin@armorofgod.org")

print("✨ Database is ready for use!")

# Close connection
client.close()
import os
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path

# Global Firebase app instance
_firebase_app = None
_db = None

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    global _firebase_app, _db
    
    if _firebase_app is not None:
        return _firebase_app
    
    try:
        # Look for service account key file
        current_dir = Path(__file__).parent.parent  # Go up to project root
        service_account_path = current_dir / "firebase_config.json"
        
        if not service_account_path.exists():
            raise FileNotFoundError(
                f"Firebase service account key not found at {service_account_path}. "
                "Please download your service account key from Firebase Console and "
                "save it as 'firebase_config.json' in your project root."
            )
        
        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(str(service_account_path))
        _firebase_app = firebase_admin.initialize_app(cred)
        
        # Initialize Firestore client only
        _db = firestore.client()
        # _bucket = storage.bucket()  # Skip storage for now
        
        print(f"✅ Firebase initialized successfully!")
        print(f"   Project ID: {get_project_id(service_account_path)}")
        print(f"   Database: {_db.project}")

        
        return _firebase_app
        
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        raise

def get_project_id(service_account_path):
    """Extract project ID from service account file"""
    import json
    with open(service_account_path, 'r') as f:
        data = json.load(f)
        return data.get('project_id')

def get_db():
    """Get Firestore database client"""
    if _db is None:
        initialize_firebase()
    return _db

def test_connection():
    """Test Firebase connection"""
    try:
        db = get_db()
        
        # Test Firestore
        test_doc = db.collection('test').document('connection_test')
        test_doc.set({'status': 'connected', 'timestamp': firestore.SERVER_TIMESTAMP})
        
        # Read it back
        doc = test_doc.get()
        if doc.exists:
            print("✅ Firestore connection: OK")
            # Clean up test document
            test_doc.delete()
            return True
        else:
            print("❌ Firestore connection: Failed")
            return False
        
    except Exception as e:
        print(f"❌ Firebase connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Firebase connection...")
    initialize_firebase()
    test_connection()
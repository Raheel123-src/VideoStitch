import firebase_admin
from firebase_admin import credentials, firestore
from typing import Dict, Optional, List
import time
import json
from datetime import datetime, timedelta

class FirebaseSessionManager:
    """Manages video stitching sessions using Firebase Firestore"""
    
    def __init__(self):
        """Initialize Firebase connection"""
        try:
            # Try to get existing app
            self.app = firebase_admin.get_app()
        except ValueError:
            # Initialize new app if none exists
            try:
                # Try to use service account key file
                cred = credentials.Certificate("serviceAccountKey.json")
                self.app = firebase_admin.initialize_app(cred)
            except FileNotFoundError:
                # Use default credentials (for Modal deployment)
                self.app = firebase_admin.initialize_app()
        
        self.db = firestore.client()
        self.sessions_collection = self.db.collection('video_sessions')
        
    def create_session(self, session_id: str, videos: List[dict], voice_url: Optional[str] = None, 
                      voice_volume: float = 1.0, mode: str = "portrait", bgm_enabled: bool = False,
                      bgm_category: Optional[str] = None, bgm_volume: float = 0.3) -> bool:
        """Create a new session in Firestore"""
        try:
            session_data = {
                'session_id': session_id,
                'status': 'processing',
                'progress': 0,
                'message': 'Session created, starting video processing...',
                'videos': videos,
                'voice_url': voice_url,
                'voice_volume': voice_volume,
                'mode': mode,
                'bgm_enabled': bgm_enabled,
                'bgm_category': bgm_category,
                'bgm_volume': bgm_volume,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                's3_url': None,
                'error': None
            }
            
            self.sessions_collection.document(session_id).set(session_data)
            print(f"✅ Session {session_id} created in Firebase")
            return True
            
        except Exception as e:
            print(f"❌ Error creating session in Firebase: {str(e)}")
            return False
    
    def update_session_status(self, session_id: str, status: str, progress: int, 
                            message: str, s3_url: Optional[str] = None, error: Optional[str] = None) -> bool:
        """Update session status in Firestore"""
        try:
            update_data = {
                'status': status,
                'progress': progress,
                'message': message,
                'updated_at': datetime.utcnow()
            }
            
            if s3_url is not None:
                update_data['s3_url'] = s3_url
                
            if error is not None:
                update_data['error'] = error
                update_data['status'] = 'failed'
            
            self.sessions_collection.document(session_id).update(update_data)
            print(f"✅ Session {session_id} status updated: {status} - {progress}%")
            return True
            
        except Exception as e:
            print(f"❌ Error updating session status in Firebase: {str(e)}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data from Firestore"""
        try:
            doc = self.sessions_collection.document(session_id).get()
            if doc.exists:
                session_data = doc.to_dict()
                # Convert datetime objects to timestamps for JSON serialization
                if 'created_at' in session_data:
                    session_data['created_at'] = session_data['created_at'].isoformat()
                if 'updated_at' in session_data:
                    session_data['updated_at'] = session_data['updated_at'].isoformat()
                return session_data
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error getting session from Firebase: {str(e)}")
            return None
    
    def list_sessions(self, limit: int = 50) -> List[Dict]:
        """List recent sessions from Firestore"""
        try:
            sessions = []
            docs = self.sessions_collection.order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit).stream()
            
            for doc in docs:
                session_data = doc.to_dict()
                # Convert datetime objects to timestamps
                if 'created_at' in session_data:
                    session_data['created_at'] = session_data['created_at'].isoformat()
                if 'updated_at' in session_data:
                    session_data['updated_at'] = session_data['updated_at'].isoformat()
                sessions.append(session_data)
            
            return sessions
            
        except Exception as e:
            print(f"❌ Error listing sessions from Firebase: {str(e)}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session from Firestore"""
        try:
            self.sessions_collection.document(session_id).delete()
            print(f"✅ Session {session_id} deleted from Firebase")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting session from Firebase: {str(e)}")
            return False
    
    def cleanup_old_sessions(self, days_old: int = 7) -> int:
        """Clean up old completed/failed sessions"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days_old)
            
            # Query for old sessions
            old_sessions = self.sessions_collection.where('status', 'in', ['completed', 'failed'])\
                                                  .where('updated_at', '<', cutoff_time)\
                                                  .stream()
            
            deleted_count = 0
            for doc in old_sessions:
                doc.reference.delete()
                deleted_count += 1
            
            print(f"✅ Cleaned up {deleted_count} old sessions from Firebase")
            return deleted_count
            
        except Exception as e:
            print(f"❌ Error cleaning up old sessions from Firebase: {str(e)}")
            return 0
    
    def get_session_stats(self) -> Dict:
        """Get statistics about sessions"""
        try:
            total_sessions = len(list(self.sessions_collection.stream()))
            
            # Count by status
            status_counts = {}
            for status in ['processing', 'completed', 'failed']:
                count = len(list(self.sessions_collection.where('status', '==', status).stream()))
                status_counts[status] = count
            
            return {
                'total_sessions': total_sessions,
                'status_counts': status_counts,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting session stats from Firebase: {str(e)}")
            return {}

# Global instance
session_manager = FirebaseSessionManager()

# Convenience functions
def create_session(session_id: str, **kwargs) -> bool:
    """Create a new session"""
    return session_manager.create_session(session_id, **kwargs)

def update_session_status(session_id: str, status: str = None, progress: int = None, 
                         message: str = None, s3_url: str = None, error: str = None) -> bool:
    """Update session status with required parameters"""
    kwargs = {}
    if status is not None:
        kwargs['status'] = status
    if progress is not None:
        kwargs['progress'] = progress
    if message is not None:
        kwargs['message'] = message
    if s3_url is not None:
        kwargs['s3_url'] = s3_url
    if error is not None:
        kwargs['error'] = error
    
    return session_manager.update_session_status(session_id, **kwargs)

def get_session(session_id: str) -> Optional[Dict]:
    """Get session data"""
    return session_manager.get_session(session_id)

def list_sessions(limit: int = 50) -> List[Dict]:
    """List sessions"""
    return session_manager.list_sessions(limit)

def delete_session(session_id: str) -> bool:
    """Delete session"""
    return session_manager.delete_session(session_id)

def cleanup_old_sessions(days_old: int = 7) -> int:
    """Clean up old sessions"""
    return session_manager.cleanup_old_sessions(days_old)

def get_session_stats() -> Dict:
    """Get session statistics"""
    return session_manager.get_session_stats()

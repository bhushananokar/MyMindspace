"""
AI Therapy System - Utilities Module
Provides date/time helpers, validation, logging, backup, export, and security utilities
"""

import os
import re
import json
import shutil
import logging
import hashlib
import zipfile
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import sqlite3
from cryptography.fernet import Fernet
import base64


# =============================================================================
# Logging and Monitoring Setup
# =============================================================================

def setup_logging(log_level: str = 'INFO', log_file: str = 'therapy_system.log') -> logging.Logger:
    """Set up comprehensive logging system"""
    
    # Create logger
    logger = logging.getLogger('therapy_system')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s'
    )
    
    # File handler with rotation
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def log_action(action: str, module: str, level: str = 'INFO', 
               patient_id: Optional[int] = None, session_id: Optional[int] = None,
               additional_data: Optional[Dict[str, Any]] = None) -> None:
    """Log system actions with context"""
    
    logger = logging.getLogger('therapy_system')
    
    # Build log message
    log_data = {
        'action': action,
        'module': module,
        'timestamp': datetime.now().isoformat(),
        'patient_id': patient_id,
        'session_id': session_id
    }
    
    if additional_data:
        log_data.update(additional_data)
    
    # Create message
    message = f"{module.upper()}: {action}"
    if patient_id:
        message += f" [Patient: {patient_id}]"
    if session_id:
        message += f" [Session: {session_id}]"
    
    # Log at specified level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.log(log_level, message, extra={'log_data': log_data})
    
    # Store in database if available
    try:
        from database import TherapyDatabase
        db = TherapyDatabase()
        db.execute_update('''
            INSERT INTO system_logs (log_level, module, action, patient_id, session_id, message, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (level, module, action, patient_id, session_id, message, datetime.now().isoformat()))
    except Exception:
        pass  # Don't fail if database logging fails


def monitor_system_health() -> Dict[str, Any]:
    """Monitor system health and performance"""
    
    health_data = {
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy',
        'checks': {},
        'warnings': [],
        'errors': []
    }
    
    # Check disk space
    try:
        total, used, free = shutil.disk_usage('.')
        free_percent = (free / total) * 100
        health_data['checks']['disk_space'] = {
            'free_gb': round(free / (1024**3), 2),
            'free_percent': round(free_percent, 1),
            'status': 'ok' if free_percent > 10 else 'warning'
        }
        
        if free_percent < 10:
            health_data['warnings'].append('Low disk space warning')
        if free_percent < 5:
            health_data['errors'].append('Critical disk space')
            health_data['status'] = 'critical'
    except Exception as e:
        health_data['errors'].append(f'Disk space check failed: {e}')
    
    # Check database connectivity
    try:
        from database import TherapyDatabase
        db = TherapyDatabase()
        with db.get_connection() as conn:
            conn.execute("SELECT 1").fetchone()
        health_data['checks']['database'] = {'status': 'ok'}
    except Exception as e:
        health_data['checks']['database'] = {'status': 'error', 'message': str(e)}
        health_data['errors'].append(f'Database connectivity issue: {e}')
        health_data['status'] = 'critical'
    
    # Check log file size
    try:
        log_file = 'therapy_system.log'
        if os.path.exists(log_file):
            log_size_mb = os.path.getsize(log_file) / (1024**2)
            health_data['checks']['log_file'] = {
                'size_mb': round(log_size_mb, 2),
                'status': 'ok' if log_size_mb < 50 else 'warning'
            }
            
            if log_size_mb > 50:
                health_data['warnings'].append('Large log file size')
        else:
            health_data['checks']['log_file'] = {'status': 'missing'}
    except Exception as e:
        health_data['errors'].append(f'Log file check failed: {e}')
    
    return health_data


# =============================================================================
# Date and Time Helpers
# =============================================================================

def format_datetime(dt: Union[datetime, str], format_type: str = 'default') -> str:
    """Format datetime with various options"""
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt  # Return as-is if can't parse
    
    formats = {
        'default': '%Y-%m-%d %H:%M:%S',
        'date_only': '%Y-%m-%d',
        'time_only': '%H:%M:%S',
        'friendly': '%B %d, %Y at %I:%M %p',
        'short': '%m/%d/%y %H:%M',
        'iso': '%Y-%m-%dT%H:%M:%S',
        'clinical': '%d-%b-%Y %H:%M'
    }
    
    return dt.strftime(formats.get(format_type, formats['default']))


def parse_date_input(date_input: str) -> Optional[date]:
    """Parse various date input formats"""
    
    if not date_input or not isinstance(date_input, str):
        return None
    
    # Common date formats to try
    formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%m-%d-%Y',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%B %d, %Y',
        '%b %d, %Y',
        '%Y%m%d'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_input.strip(), fmt).date()
        except ValueError:
            continue
    
    return None


def calculate_age(birth_date: Union[date, str]) -> Optional[int]:
    """Calculate age from birth date"""
    
    if isinstance(birth_date, str):
        birth_date = parse_date_input(birth_date)
    
    if not birth_date:
        return None
    
    today = date.today()
    age = today.year - birth_date.year
    
    # Adjust if birthday hasn't occurred this year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    return max(0, age)  # Ensure non-negative age


def get_session_duration_display(start_time: datetime, end_time: Optional[datetime] = None) -> str:
    """Get human-readable session duration"""
    
    if end_time is None:
        end_time = datetime.now()
    
    duration = end_time - start_time
    total_minutes = int(duration.total_seconds() / 60)
    
    if total_minutes < 60:
        return f"{total_minutes} minutes"
    else:
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}h {minutes}m"


def is_business_hours(dt: Optional[datetime] = None) -> bool:
    """Check if datetime falls within business hours (9 AM - 5 PM, Mon-Fri)"""
    
    if dt is None:
        dt = datetime.now()
    
    # Check if weekday (0=Monday, 6=Sunday)
    if dt.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Check if within business hours
    return 9 <= dt.hour < 17


# =============================================================================
# Text Processing and Validation
# =============================================================================

def sanitize_input(text: str, max_length: int = 1000, allow_html: bool = False) -> str:
    """Sanitize and validate text input"""
    
    if not isinstance(text, str):
        return ""
    
    # Remove null bytes and normalize whitespace
    text = text.replace('\x00', '').strip()
    
    # Remove HTML if not allowed
    if not allow_html:
        text = re.sub(r'<[^>]+>', '', text)
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length].rstrip()
    
    return text


def validate_email(email: str) -> bool:
    """Validate email address format"""
    
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check for valid length (10-15 digits)
    return 10 <= len(digits_only) <= 15


def format_phone(phone: str) -> str:
    """Format phone number consistently"""
    
    if not validate_phone(phone):
        return phone
    
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 10:
        # US format: (123) 456-7890
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        # US with country code: +1 (123) 456-7890
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        # International format: +XX-XXX-XXX-XXXX
        return f"+{digits}"


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """Extract meaningful keywords from text"""
    
    if not text:
        return []
    
    # Remove punctuation and convert to lowercase
    cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Split into words and filter
    words = [word.strip() for word in cleaned.split()]
    
    # Common stop words to exclude
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
    }
    
    keywords = [
        word for word in words 
        if len(word) >= min_length and word not in stop_words
    ]
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(keywords))


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity score (0-1)"""
    
    if not text1 or not text2:
        return 0.0
    
    keywords1 = set(extract_keywords(text1))
    keywords2 = set(extract_keywords(text2))
    
    if not keywords1 and not keywords2:
        return 1.0 if text1.strip() == text2.strip() else 0.0
    
    if not keywords1 or not keywords2:
        return 0.0
    
    intersection = keywords1 & keywords2
    union = keywords1 | keywords2
    
    return len(intersection) / len(union) if union else 0.0


# =============================================================================
# Security and Encryption Helpers
# =============================================================================

class EncryptionHelper:
    """Simple encryption/decryption for sensitive data"""
    
    def __init__(self, key: Optional[str] = None):
        if key:
            # Use provided key
            key_bytes = key.encode()[:32].ljust(32, b'0')  # Ensure 32 bytes
            self.key = base64.urlsafe_b64encode(key_bytes)
        else:
            # Generate new key
            self.key = Fernet.generate_key()
        
        self.fernet = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        if not data:
            return ""
        
        encrypted = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        if not encrypted_data:
            return ""
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception:
            return ""  # Return empty string if decryption fails
    
    def get_key_string(self) -> str:
        """Get key as string for storage"""
        return self.key.decode()


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Hash password with salt"""
    
    if salt is None:
        salt = os.urandom(32).hex()
    
    pwdhash = hashlib.pbkdf2_hmac('sha256', 
                                 password.encode('utf-8'), 
                                 salt.encode('utf-8'), 
                                 100000)  # 100k iterations
    
    return pwdhash.hex(), salt


def verify_password(stored_hash: str, stored_salt: str, password: str) -> bool:
    """Verify password against stored hash"""
    
    pwdhash, _ = hash_password(password, stored_salt)
    return pwdhash == stored_hash


def generate_session_token() -> str:
    """Generate secure session token"""
    
    return os.urandom(32).hex()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    
    # Remove/replace dangerous characters
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    safe_filename = safe_filename.strip('. ')
    
    # Limit length
    if len(safe_filename) > 200:
        name, ext = os.path.splitext(safe_filename)
        safe_filename = name[:200-len(ext)] + ext
    
    return safe_filename or 'unnamed_file'


# =============================================================================
# Backup and Recovery Functions
# =============================================================================

def create_system_backup(backup_dir: str = 'backups') -> str:
    """Create comprehensive system backup"""
    
    # Create backup directory
    backup_path = Path(backup_dir)
    backup_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_path / f'therapy_system_backup_{timestamp}.zip'
    
    try:
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            
            # Backup database
            if os.path.exists('therapy.db'):
                zipf.write('therapy.db', 'therapy.db')
            
            # Backup configuration files
            config_files = ['config.py', 'requirements.txt']
            for config_file in config_files:
                if os.path.exists(config_file):
                    zipf.write(config_file, config_file)
            
            # Backup log files
            for log_file in Path('.').glob('*.log'):
                zipf.write(log_file, log_file.name)
            
            # Add backup metadata
            metadata = {
                'backup_created': datetime.now().isoformat(),
                'system_version': '1.0.0',
                'backup_type': 'full_system'
            }
            
            zipf.writestr('backup_metadata.json', json.dumps(metadata, indent=2))
        
        log_action(f"System backup created: {backup_file}", "backup")
        return str(backup_file)
        
    except Exception as e:
        log_action(f"Backup creation failed: {e}", "backup", "ERROR")
        raise


def restore_system_backup(backup_file: str) -> bool:
    """Restore system from backup file"""
    
    if not os.path.exists(backup_file):
        raise FileNotFoundError(f"Backup file not found: {backup_file}")
    
    try:
        # Create safety backup of current state
        safety_backup = create_system_backup('temp_backups')
        
        with zipfile.ZipFile(backup_file, 'r') as zipf:
            
            # Extract all files
            zipf.extractall('.')
            
            # Verify backup metadata
            if 'backup_metadata.json' in zipf.namelist():
                metadata_content = zipf.read('backup_metadata.json').decode()
                metadata = json.loads(metadata_content)
                log_action(f"Restoring backup from {metadata.get('backup_created')}", "restore")
        
        log_action(f"System restored from backup: {backup_file}", "restore")
        return True
        
    except Exception as e:
        log_action(f"Restore failed: {e}", "restore", "ERROR")
        raise


def cleanup_old_backups(backup_dir: str = 'backups', days_to_keep: int = 30) -> int:
    """Clean up old backup files"""
    
    if not os.path.exists(backup_dir):
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    deleted_count = 0
    
    for backup_file in Path(backup_dir).glob('*.zip'):
        if backup_file.stat().st_mtime < cutoff_date.timestamp():
            try:
                backup_file.unlink()
                deleted_count += 1
                log_action(f"Deleted old backup: {backup_file.name}", "cleanup")
            except Exception as e:
                log_action(f"Failed to delete backup {backup_file.name}: {e}", "cleanup", "WARNING")
    
    return deleted_count


# =============================================================================
# Data Export Utilities
# =============================================================================

def export_patient_data(patient_id: int, export_format: str = 'json') -> str:
    """Export patient data in specified format"""
    
    try:
        from database import TherapyDatabase
        db = TherapyDatabase()
        
        # Get comprehensive patient data
        patient_data = db.export_patient_data(patient_id)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if export_format.lower() == 'json':
            filename = f'patient_{patient_id}_export_{timestamp}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(patient_data, f, indent=2, default=str)
        
        elif export_format.lower() == 'csv':
            import csv
            filename = f'patient_{patient_id}_export_{timestamp}.csv'
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write patient basic info
                if patient_data.get('patient_info'):
                    patient = patient_data['patient_info'][0]
                    writer.writerow(['Patient Information'])
                    for key, value in patient.items():
                        writer.writerow([key, value])
                    writer.writerow([])  # Empty row
                
                # Write sessions summary
                writer.writerow(['Sessions Summary'])
                if patient_data.get('sessions'):
                    sessions = patient_data['sessions']
                    if sessions:
                        writer.writerow(sessions[0].keys())
                        for session in sessions:
                            writer.writerow(session.values())
        
        else:
            raise ValueError(f"Unsupported export format: {export_format}")
        
        log_action(f"Patient data exported: {filename}", "export", patient_id=patient_id)
        return filename
        
    except Exception as e:
        log_action(f"Data export failed for patient {patient_id}: {e}", "export", "ERROR")
        raise


def generate_system_report() -> Dict[str, Any]:
    """Generate comprehensive system usage report"""
    
    try:
        from database import TherapyDatabase
        db = TherapyDatabase()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {},
            'patient_stats': {},
            'session_stats': {},
            'assessment_stats': {},
            'system_health': monitor_system_health()
        }
        
        # Patient statistics
        patient_count = db.execute_query("SELECT COUNT(*) as count FROM patients")[0]['count']
        active_patients = db.execute_query(
            "SELECT COUNT(*) as count FROM patients WHERE last_updated > ?",
            ((datetime.now() - timedelta(days=30)).isoformat(),)
        )[0]['count']
        
        report['patient_stats'] = {
            'total_patients': patient_count,
            'active_patients_30_days': active_patients,
            'patient_activity_rate': round((active_patients / patient_count * 100), 1) if patient_count > 0 else 0
        }
        
        # Session statistics
        total_sessions = db.execute_query("SELECT COUNT(*) as count FROM sessions")[0]['count']
        recent_sessions = db.execute_query(
            "SELECT COUNT(*) as count FROM sessions WHERE session_date > ?",
            ((datetime.now() - timedelta(days=7)).isoformat(),)
        )[0]['count']
        
        report['session_stats'] = {
            'total_sessions': total_sessions,
            'sessions_last_week': recent_sessions,
            'avg_sessions_per_patient': round(total_sessions / patient_count, 1) if patient_count > 0 else 0
        }
        
        # Assessment statistics
        total_assessments = db.execute_query("SELECT COUNT(*) as count FROM assessments")[0]['count']
        
        report['assessment_stats'] = {
            'total_assessments': total_assessments,
            'avg_assessments_per_patient': round(total_assessments / patient_count, 1) if patient_count > 0 else 0
        }
        
        # Summary
        report['summary'] = {
            'system_status': 'operational',
            'data_points': patient_count + total_sessions + total_assessments,
            'utilization_trend': 'stable'  # Could be calculated based on recent activity
        }
        
        return report
        
    except Exception as e:
        log_action(f"System report generation failed: {e}", "reporting", "ERROR")
        raise


# =============================================================================
# Utility Testing and Validation
# =============================================================================

def validate_system_requirements() -> Dict[str, bool]:
    """Validate that system requirements are met"""
    
    requirements = {
        'python_version': False,
        'required_modules': False,
        'database_accessible': False,
        'log_directory_writable': False,
        'backup_directory_writable': False
    }
    
    # Check Python version
    import sys
    if sys.version_info >= (3, 8):
        requirements['python_version'] = True
    
    # Check required modules
    try:
        import sqlite3
        from cryptography.fernet import Fernet
        requirements['required_modules'] = True
    except ImportError:
        pass
    
    # Check database accessibility
    try:
        conn = sqlite3.connect(':memory:')
        conn.execute("SELECT 1")
        conn.close()
        requirements['database_accessible'] = True
    except Exception:
        pass
    
    # Check directory permissions
    try:
        test_file = 'test_write_permission.tmp'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        requirements['log_directory_writable'] = True
    except Exception:
        pass
    
    try:
        os.makedirs('backups', exist_ok=True)
        requirements['backup_directory_writable'] = True
    except Exception:
        pass
    
    return requirements


# Module testing function
def main():
    """Test utility functions"""
    print("Therapy System Utilities Test")
    print("=" * 50)
    
    # Test logging setup
    logger = setup_logging('DEBUG')
    print("✓ Logging system initialized")
    
    # Test date formatting
    now = datetime.now()
    print(f"✓ Current time (friendly): {format_datetime(now, 'friendly')}")
    print(f"✓ Current time (clinical): {format_datetime(now, 'clinical')}")
    
    # Test age calculation
    test_birth = date(1990, 5, 15)
    age = calculate_age(test_birth)
    print(f"✓ Age calculation: {age} years old")
    
    # Test validation
    print(f"✓ Email validation: {validate_email('test@example.com')}")
    print(f"✓ Phone validation: {validate_phone('(555) 123-4567')}")
    
    # Test text processing
    test_text = "This is a sample text for keyword extraction!"
    keywords = extract_keywords(test_text)
    print(f"✓ Keywords extracted: {keywords}")
    
    # Test encryption
    encryptor = EncryptionHelper()
    test_data = "Sensitive patient information"
    encrypted = encryptor.encrypt(test_data)
    decrypted = encryptor.decrypt(encrypted)
    print(f"✓ Encryption test: {'PASS' if decrypted == test_data else 'FAIL'}")
    
    # Test system requirements
    requirements = validate_system_requirements()
    all_met = all(requirements.values())
    print(f"✓ System requirements: {'All met' if all_met else 'Some missing'}")
    
    # Test system health
    health = monitor_system_health()
    print(f"✓ System health: {health['status']}")
    
    print("\nUtilities test completed!")


if __name__ == "__main__":
    main()
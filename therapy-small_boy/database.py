#!/usr/bin/env python3
"""
AI Therapy System - Database Management
SQLite database operations, schema management, and data integrity
"""

import sqlite3
import json
import os
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
from contextlib import contextmanager
import threading
from pathlib import Path

try:
    from config import Config
except ImportError:
    # Fallback configuration if config.py doesn't exist yet
    class Config:
        DATABASE_PATH = "therapy.db"
        LOG_LEVEL = "INFO"

try:
    from utils import log_action
except ImportError:
    # Fallback logging if utils.py doesn't exist yet
    def log_action(message, module, level="INFO", **kwargs):
        print(f"[{level}] {module}: {message}")


class TherapyDatabase:
    """Main database class for the therapy system"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.lock = threading.Lock()
        
    def initialize_database(self):
        """Initialize database with complete schema"""
        with self.get_connection() as conn:
            # Enable foreign keys and optimization
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            
            self._create_all_tables(conn)
            self._create_indexes(conn)
            log_action("Database initialized successfully", "database")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
            # Only commit if connection is still open
            if conn and not hasattr(conn, '_closed') or not getattr(conn, '_closed', False):
                conn.commit()
        except Exception as e:
            # Only rollback if connection is still open
            if conn and not hasattr(conn, '_closed') or not getattr(conn, '_closed', False):
                try:
                    conn.rollback()
                except sqlite3.ProgrammingError:
                    pass  # Connection already closed
            raise e
        finally:
            if conn:
                try:
                    conn.close()
                except sqlite3.ProgrammingError:
                    pass  # Connection already closed
    
    def _create_all_tables(self, conn: sqlite3.Connection):
        """Create all database tables"""
        
        # Patients table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date_of_birth TEXT,
                gender TEXT,
                contact_info TEXT,
                emergency_contact TEXT,
                created_date TEXT NOT NULL DEFAULT (datetime('now')),
                last_updated TEXT NOT NULL DEFAULT (datetime('now')),
                risk_level TEXT DEFAULT 'low' CHECK (risk_level IN ('low', 'moderate', 'high', 'imminent')),
                preferred_therapy_mode TEXT DEFAULT 'CBT',
                notes TEXT,
                active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Sessions table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                session_date TEXT NOT NULL DEFAULT (datetime('now')),
                session_type TEXT CHECK (session_type IN ('CBT', 'DBT', 'ACT', 'Psychodynamic', 'Assessment', 'Crisis')),
                duration INTEGER DEFAULT 50,
                mood_before INTEGER CHECK (mood_before BETWEEN 1 AND 10),
                mood_after INTEGER CHECK (mood_after BETWEEN 1 AND 10),
                interventions_used TEXT DEFAULT '[]',
                homework_assigned TEXT,
                crisis_flags TEXT DEFAULT '[]',
                therapist_notes TEXT,
                patient_feedback TEXT,
                session_phase TEXT DEFAULT 'completed',
                completed BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        ''')
        
        # Assessments table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                session_id INTEGER,
                assessment_type TEXT NOT NULL CHECK (assessment_type IN ('PHQ9', 'GAD7', 'PCL5', 'ORS', 'SRS')),
                questions_responses TEXT NOT NULL DEFAULT '{}',
                total_score INTEGER NOT NULL DEFAULT 0,
                severity_level TEXT,
                assessment_date TEXT NOT NULL DEFAULT (datetime('now')),
                interpretation TEXT,
                administered_by TEXT DEFAULT 'AI_System',
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
            )
        ''')
        
        # Diagnoses table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS diagnoses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                diagnosis_code TEXT,
                diagnosis_name TEXT NOT NULL,
                severity TEXT CHECK (severity IN ('mild', 'moderate', 'severe', 'in_partial_remission', 'in_full_remission')),
                date_diagnosed TEXT NOT NULL DEFAULT (datetime('now')),
                date_resolved TEXT,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'in_remission', 'resolved', 'rule_out')),
                supporting_criteria TEXT DEFAULT '{}',
                notes TEXT,
                diagnosed_by TEXT DEFAULT 'AI_System',
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        ''')
        
        # Treatment Goals table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS treatment_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                goal_type TEXT CHECK (goal_type IN ('symptom', 'functional', 'behavioral')),
                goal_description TEXT NOT NULL,
                target_date TEXT,
                current_progress INTEGER DEFAULT 0 CHECK (current_progress BETWEEN 0 AND 100),
                measurement_criteria TEXT,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'achieved', 'modified', 'discontinued')),
                created_date TEXT NOT NULL DEFAULT (datetime('now')),
                last_updated TEXT NOT NULL DEFAULT (datetime('now')),
                notes TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        ''')
        
        # Homework Assignments table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS homework_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                session_id INTEGER,
                assignment_type TEXT,
                description TEXT NOT NULL,
                instructions TEXT,
                assigned_date TEXT NOT NULL DEFAULT (datetime('now')),
                due_date TEXT,
                completed BOOLEAN DEFAULT FALSE,
                completion_date TEXT,
                completion_notes TEXT,
                effectiveness_rating INTEGER CHECK (effectiveness_rating BETWEEN 1 AND 5),
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
            )
        ''')
        
        # Progress Notes table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS progress_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                session_id INTEGER,
                note_type TEXT DEFAULT 'progress' CHECK (note_type IN ('SOAP', 'progress', 'crisis', 'assessment')),
                subjective TEXT,
                objective TEXT,
                assessment TEXT,
                plan TEXT,
                created_date TEXT NOT NULL DEFAULT (datetime('now')),
                created_by TEXT DEFAULT 'AI_Therapist',
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        ''')
        
        # Treatment Plans table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS treatment_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                plan_name TEXT NOT NULL,
                primary_modality TEXT CHECK (primary_modality IN ('CBT', 'DBT', 'ACT', 'Psychodynamic')),
                target_symptoms TEXT DEFAULT '[]',
                treatment_goals TEXT DEFAULT '[]',
                estimated_duration INTEGER,
                session_frequency TEXT DEFAULT 'weekly',
                created_date TEXT NOT NULL DEFAULT (datetime('now')),
                last_reviewed TEXT,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'modified', 'discontinued')),
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        ''')
        
        # Crisis Plans table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS crisis_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                warning_signs TEXT DEFAULT '[]',
                coping_strategies TEXT DEFAULT '[]',
                support_contacts TEXT DEFAULT '[]',
                professional_contacts TEXT DEFAULT '[]',
                safety_restrictions TEXT,
                created_date TEXT NOT NULL DEFAULT (datetime('now')),
                last_updated TEXT NOT NULL DEFAULT (datetime('now')),
                active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        ''')
        
        # System Logs table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_level TEXT NOT NULL,
                module TEXT NOT NULL,
                action TEXT NOT NULL,
                patient_id INTEGER,
                session_id INTEGER,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                additional_data TEXT DEFAULT '{}'
            )
        ''')
    
    def _create_indexes(self, conn: sqlite3.Connection):
        """Create database indexes for performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name)",
            "CREATE INDEX IF NOT EXISTS idx_patients_active ON patients(active)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_patient_date ON sessions(patient_id, session_date)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_type ON sessions(session_type)",
            "CREATE INDEX IF NOT EXISTS idx_assessments_patient_type ON assessments(patient_id, assessment_type)",
            "CREATE INDEX IF NOT EXISTS idx_assessments_date ON assessments(assessment_date)",
            "CREATE INDEX IF NOT EXISTS idx_goals_patient_status ON treatment_goals(patient_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_homework_patient_due ON homework_assignments(patient_id, due_date)",
            "CREATE INDEX IF NOT EXISTS idx_homework_completed ON homework_assignments(completed)",
            "CREATE INDEX IF NOT EXISTS idx_notes_patient_date ON progress_notes(patient_id, created_date)",
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(log_level)",
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(index_sql)
            except sqlite3.Error as e:
                log_action(f"Index creation warning: {e}", "database", "WARNING")
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dicts"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return last row ID or rows affected"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            if query.strip().upper().startswith('INSERT'):
                return cursor.lastrowid
            else:
                return cursor.rowcount
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'database_file': self.db_path
        }
        
        try:
            # Get table row counts
            tables = ['patients', 'sessions', 'assessments', 'treatment_goals', 
                     'homework_assignments', 'progress_notes', 'system_logs']
            
            for table in tables:
                try:
                    result = self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                    stats[f'{table}_count'] = result[0]['count'] if result else 0
                except sqlite3.Error:
                    stats[f'{table}_count'] = 0
            
            # Get database file size
            if os.path.exists(self.db_path):
                stats['file_size_mb'] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
            else:
                stats['file_size_mb'] = 0
            
            # Get database info
            with self.get_connection() as conn:
                # Database page count and size
                page_count = conn.execute("PRAGMA page_count").fetchone()[0]
                page_size = conn.execute("PRAGMA page_size").fetchone()[0]
                stats['total_pages'] = page_count
                stats['page_size'] = page_size
                stats['calculated_size_mb'] = round((page_count * page_size) / (1024 * 1024), 2)
                
        except Exception as e:
            log_action(f"Error getting database stats: {e}", "database", "ERROR")
            
        return stats
    
    def backup_database(self, backup_path: str = None) -> str:
        """Create a backup of the database"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = "backups"
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, f"therapy_backup_{timestamp}.db")
        
        try:
            # Ensure source database exists
            if not os.path.exists(self.db_path):
                log_action(f"Source database {self.db_path} does not exist", "database", "WARNING")
                return backup_path
            
            shutil.copy2(self.db_path, backup_path)
            log_action(f"Database backup created: {backup_path}", "database")
            return backup_path
        except Exception as e:
            log_action(f"Database backup failed: {e}", "database", "ERROR")
            raise
    
    def validate_database_integrity(self) -> Dict[str, Any]:
        """Validate database integrity"""
        integrity_results = {
            'timestamp': datetime.now().isoformat(),
            'integrity_check': [],
            'foreign_key_check': [],
            'issues_found': False
        }
        
        try:
            with self.get_connection() as conn:
                # PRAGMA integrity_check
                integrity = conn.execute("PRAGMA integrity_check").fetchall()
                integrity_results['integrity_check'] = [row[0] for row in integrity]
                
                # PRAGMA foreign_key_check (only if foreign keys are enabled)
                fk_check = conn.execute("PRAGMA foreign_key_check").fetchall()
                integrity_results['foreign_key_check'] = [dict(row) for row in fk_check]
                
                # Check if any issues found
                if integrity_results['integrity_check'] != ['ok'] or integrity_results['foreign_key_check']:
                    integrity_results['issues_found'] = True
                    
        except Exception as e:
            log_action(f"Database integrity check failed: {e}", "database", "ERROR")
            integrity_results['error'] = str(e)
            integrity_results['issues_found'] = True
        
        return integrity_results
    
    def export_patient_data(self, patient_id: int) -> Dict[str, Any]:
        """Export all data for a specific patient"""
        patient_data = {
            'export_timestamp': datetime.now().isoformat(),
            'patient_id': patient_id
        }
        
        # Define queries for patient data
        data_queries = [
            ('patient_info', "SELECT * FROM patients WHERE id = ?"),
            ('sessions', "SELECT * FROM sessions WHERE patient_id = ? ORDER BY session_date"),
            ('assessments', "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date"),
            ('diagnoses', "SELECT * FROM diagnoses WHERE patient_id = ? ORDER BY date_diagnosed"),
            ('treatment_goals', "SELECT * FROM treatment_goals WHERE patient_id = ? ORDER BY created_date"),
            ('homework_assignments', "SELECT * FROM homework_assignments WHERE patient_id = ? ORDER BY assigned_date"),
            ('progress_notes', "SELECT * FROM progress_notes WHERE patient_id = ? ORDER BY created_date"),
            ('treatment_plans', "SELECT * FROM treatment_plans WHERE patient_id = ? ORDER BY created_date"),
            ('crisis_plans', "SELECT * FROM crisis_plans WHERE patient_id = ? ORDER BY created_date")
        ]
        
        for key, query in data_queries:
            try:
                results = self.execute_query(query, (patient_id,))
                patient_data[key] = results
            except Exception as e:
                log_action(f"Error exporting {key} for patient {patient_id}: {e}", "database", "ERROR")
                patient_data[key] = []
        
        log_action(f"Patient data exported for ID {patient_id}", "database", patient_id=patient_id)
        return patient_data
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """Clean up old log entries and system data"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        cleanup_results = {}
        
        try:
            with self.get_connection() as conn:
                # Clean old system logs (keep warnings and errors longer)
                result = conn.execute(
                    "DELETE FROM system_logs WHERE timestamp < ? AND log_level IN ('DEBUG', 'INFO')",
                    (cutoff_date,)
                )
                cleanup_results['old_logs_deleted'] = result.rowcount
                
                # Update last_updated timestamp for active patients
                conn.execute(
                    "UPDATE patients SET last_updated = datetime('now') WHERE active = TRUE"
                )
                
                log_action(f"Cleaned up {cleanup_results['old_logs_deleted']} old log entries", "database")
                
        except Exception as e:
            log_action(f"Cleanup operation failed: {e}", "database", "ERROR")
            cleanup_results['error'] = str(e)
        
        return cleanup_results


class DatabaseManager(TherapyDatabase):
    """Alias class for compatibility - inherits from TherapyDatabase"""
    
    def __init__(self, db_path: str = None):
        super().__init__(db_path)


# Convenience functions for common operations
def get_or_create_patient(db: TherapyDatabase, name: str, **kwargs) -> Dict[str, Any]:
    """Get existing patient or create new one"""
    # Check if patient exists
    existing = db.execute_query("SELECT * FROM patients WHERE name = ? AND active = TRUE", (name,))
    if existing:
        return existing[0]
    
    # Create new patient
    patient_data = {
        'name': name,
        'date_of_birth': kwargs.get('date_of_birth'),
        'gender': kwargs.get('gender'),
        'contact_info': kwargs.get('contact_info'),
        'emergency_contact': kwargs.get('emergency_contact'),
        'preferred_therapy_mode': kwargs.get('preferred_therapy_mode', 'CBT'),
        'notes': kwargs.get('notes'),
        'created_date': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat(),
        'risk_level': 'low',
        'active': True
    }
    
    patient_id = db.execute_update('''
        INSERT INTO patients 
        (name, date_of_birth, gender, contact_info, emergency_contact, 
         preferred_therapy_mode, notes, created_date, last_updated, risk_level, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        patient_data['name'], patient_data['date_of_birth'], patient_data['gender'],
        patient_data['contact_info'], patient_data['emergency_contact'],
        patient_data['preferred_therapy_mode'], patient_data['notes'],
        patient_data['created_date'], patient_data['last_updated'],
        patient_data['risk_level'], patient_data['active']
    ))
    
    patient_data['id'] = patient_id
    return patient_data


def create_session_record(db: TherapyDatabase, patient_id: int, session_type: str, **kwargs) -> int:
    """Create a new session record"""
    session_id = db.execute_update('''
        INSERT INTO sessions 
        (patient_id, session_type, duration, mood_before, mood_after, 
         interventions_used, homework_assigned, crisis_flags, therapist_notes, patient_feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        patient_id,
        session_type,
        kwargs.get('duration', 50),
        kwargs.get('mood_before'),
        kwargs.get('mood_after'),
        json.dumps(kwargs.get('interventions_used', [])),
        kwargs.get('homework_assigned', ''),
        json.dumps(kwargs.get('crisis_flags', [])),
        kwargs.get('therapist_notes', ''),
        kwargs.get('patient_feedback', '')
    ))
    
    return session_id


def save_assessment_result(db: TherapyDatabase, patient_id: int, assessment_type: str, 
                          responses: Dict, total_score: int, severity: str, interpretation: str,
                          session_id: int = None) -> int:
    """Save assessment result to database"""
    assessment_id = db.execute_update('''
        INSERT INTO assessments 
        (patient_id, session_id, assessment_type, questions_responses, total_score, severity_level, interpretation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        patient_id, session_id, assessment_type, 
        json.dumps(responses), total_score, severity, interpretation
    ))
    
    return assessment_id


# Test function
def main():
    """Test database functionality"""
    print("Testing TherapyDatabase...")
    
    # Initialize database
    db = TherapyDatabase(":memory:")  # Use in-memory database for testing
    db.initialize_database()
    
    print("✅ Database initialization successful")
    
    # Test patient creation
    print("\n1. Testing patient creation...")
    patient_data = get_or_create_patient(db, "Test Patient", 
                                       date_of_birth="1990-01-01",
                                       gender="Other",
                                       preferred_therapy_mode="CBT")
    print(f"✅ Created patient: {patient_data['name']} (ID: {patient_data['id']})")
    
    # Test session creation
    print("\n2. Testing session creation...")
    session_id = create_session_record(db, patient_data['id'], "CBT", 
                                     mood_before=4, mood_after=7)
    print(f"✅ Created session ID: {session_id}")
    
    # Test assessment
    print("\n3. Testing assessment save...")
    assessment_id = save_assessment_result(db, patient_data['id'], "PHQ9", 
                                         {"q1": 2, "q2": 1}, 15, "moderate", 
                                         "Moderate depression indicated")
    print(f"✅ Created assessment ID: {assessment_id}")
    
    # Test stats
    print("\n4. Testing database stats...")
    stats = db.get_database_stats()
    print(f"✅ Database stats: {stats['patients_count']} patients, {stats['sessions_count']} sessions")
    
    # Test integrity check
    print("\n5. Testing integrity check...")
    integrity = db.validate_database_integrity()
    print(f"✅ Integrity check: {integrity['integrity_check']}")
    
    print("\n🎉 All database tests completed successfully!")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
AI Therapy System - Main Entry Point and CLI Interface
Comprehensive therapy application using Gemini 2.5 Pro as the core AI engine
"""

import os
import sys
import click
import asyncio
import json
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from tabulate import tabulate

# Import all system modules
from config import Config
from database import TherapyDatabase
from models import Patient, Session, Assessment
from session_manager import SessionManager
from assessment_system import AssessmentSystem
from therapy_modules import TherapyModuleIntegrator
from goal_manager import GoalManager
from homework_system import HomeworkSystem
from documentation import DocumentationSystem
from crisis_manager import CrisisManager
from utils import (
    setup_logging, log_action, monitor_system_health, 
    format_datetime, validate_system_requirements,
    create_system_backup, export_patient_data,
    generate_system_report
)


class TherapySystemCLI:
    """Main CLI interface for the therapy system"""
    
    def __init__(self):
        self.db = None
        self.session_manager = None
        self.assessment_system = None
        self.therapy_modules = None
        self.goal_manager = None
        self.homework_system = None
        self.documentation = None
        self.crisis_manager = None
        self.logger = None
        self.initialized = False
    
    def initialize_system(self) -> bool:
        """Initialize all system components"""
        try:
            # Setup logging first
            self.logger = setup_logging(Config.LOG_LEVEL, Config.LOG_FILE)
            self.logger.info("Initializing AI Therapy System...")
            
            # Validate system requirements
            requirements = validate_system_requirements()
            if not all(requirements.values()):
                missing = [k for k, v in requirements.items() if not v]
                self.logger.error(f"System requirements not met: {missing}")
                return False
            
            # Initialize database
            self.db = TherapyDatabase()
            self.db.initialize_database()
            
            # Initialize core components
            self.session_manager = SessionManager(self.db)
            self.assessment_system = AssessmentSystem(self.db)
            self.therapy_modules = TherapyModuleIntegrator()
            self.goal_manager = GoalManager(self.db)
            self.homework_system = HomeworkSystem(self.db)
            self.documentation = DocumentationSystem(self.db)
            self.crisis_manager = CrisisManager(self.db)
            
            # Verify Gemini API key
            if not Config.GEMINI_API_KEY or Config.GEMINI_API_KEY == 'your-api-key-here':
                self.logger.warning("Gemini API key not configured - AI features will be limited")
            
            self.initialized = True
            log_action("System initialized successfully", "main")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"System initialization failed: {e}")
            else:
                print(f"CRITICAL: System initialization failed: {e}")
            return False
    
    def shutdown_system(self):
        """Graceful system shutdown"""
        try:
            if self.session_manager:
                # End any active sessions
                active_sessions = list(self.session_manager.active_sessions.keys())
                for patient_id in active_sessions:
                    asyncio.run(self.session_manager.end_session(patient_id))
            
            if self.db:
                # Backup database
                backup_file = create_system_backup()
                log_action(f"Shutdown backup created: {backup_file}", "main")
            
            log_action("System shutdown completed", "main")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during shutdown: {e}")
    
    def check_initialization(self):
        """Check if system is properly initialized"""
        # Check if database exists and has tables
        import os
        if not os.path.exists('therapy.db'):
            click.echo("❌ System not initialized. Please run initialization first.")
            sys.exit(1)
        
        # Initialize components if they don't exist
        if not self.db:
            try:
                self.db = TherapyDatabase()
                self.session_manager = SessionManager(self.db)
                self.assessment_system = AssessmentSystem(self.db)
                self.therapy_modules = TherapyModuleIntegrator()
                self.goal_manager = GoalManager(self.db)
                self.homework_system = HomeworkSystem(self.db)
                self.documentation = DocumentationSystem(self.db)
                self.crisis_manager = CrisisManager(self.db)
                self.initialized = True
            except Exception as e:
                click.echo(f"❌ Error loading system components: {e}")
                sys.exit(1)


# Initialize global CLI instance
cli = TherapySystemCLI()


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def main(debug):
    """AI Therapy System - Comprehensive therapy application with multiple modalities"""
    if debug:
        Config.LOG_LEVEL = 'DEBUG'
    
    # Display welcome banner
    click.echo("""
╔══════════════════════════════════════════════════════════════╗
║                    AI THERAPY SYSTEM MVP                     ║
║             Comprehensive Therapy with Gemini 2.5 Pro       ║
╚══════════════════════════════════════════════════════════════╝
    """)


@main.command()
def init():
    """Initialize the therapy system"""
    click.echo("🔄 Initializing AI Therapy System...")
    
    if cli.initialize_system():
        click.echo("✅ System initialized successfully!")
        
        # Show system status
        health = monitor_system_health()
        click.echo(f"📊 System Status: {health['status'].upper()}")
        
        if health['warnings']:
            click.echo(f"⚠️  Warnings: {len(health['warnings'])}")
            for warning in health['warnings']:
                click.echo(f"   • {warning}")
        
        # Quick setup check
        patient_count = cli.db.execute_query("SELECT COUNT(*) as count FROM patients")[0]['count']
        click.echo(f"📋 Current patients in system: {patient_count}")
        
    else:
        click.echo("❌ System initialization failed. Check logs for details.")
        sys.exit(1)


@main.group()
def patient():
    """Patient management commands"""
    cli.check_initialization()


@patient.command('create')
@click.option('--name', prompt='Patient name', help='Full name of the patient')
@click.option('--dob', prompt='Date of birth (YYYY-MM-DD)', help='Date of birth')
@click.option('--gender', prompt='Gender', type=click.Choice(['Male', 'Female', 'Non-binary', 'Prefer not to say']))
@click.option('--email', prompt='Email (optional)', default='', help='Email address')
@click.option('--phone', prompt='Phone (optional)', default='', help='Phone number')
@click.option('--emergency-contact', prompt='Emergency contact (optional)', default='', help='Emergency contact info')
@click.option('--therapy-mode', prompt='Preferred therapy modality', 
              type=click.Choice(['CBT', 'DBT', 'ACT', 'Psychodynamic']), default='CBT')
def create_patient(name, dob, gender, email, phone, emergency_contact, therapy_mode):
    """Create a new patient profile"""
    try:
        # Convert gender to the format expected by the database
        gender_mapping = {
            'Male': 'male',
            'Female': 'female', 
            'Non-binary': 'non_binary',
            'Prefer not to say': 'prefer_not_to_say'
        }
        db_gender = gender_mapping.get(gender, gender.lower())
        
        # Prepare contact info
        contact_info = []
        if email:
            contact_info.append(f"Email: {email}")
        if phone:
            contact_info.append(f"Phone: {phone}")
        
        # Create patient object
        patient = Patient(
            name=name,
            date_of_birth=dob,
            gender=db_gender,
            contact_info="; ".join(contact_info) if contact_info else None,
            emergency_contact=emergency_contact if emergency_contact else None,
            preferred_therapy_mode=therapy_mode
        )
        
        # Validate patient data
        patient.validate()
        
        # Save to database
        patient_data = patient.to_dict()
        patient_data.pop('id', None)  # Remove id for insert
        
        patient_id = cli.db.execute_update('''
            INSERT INTO patients 
            (name, date_of_birth, gender, contact_info, emergency_contact, 
             created_date, last_updated, risk_level, preferred_therapy_mode, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_data['name'], patient_data['date_of_birth'], patient_data['gender'],
            patient_data['contact_info'], patient_data['emergency_contact'],
            patient_data['created_date'], patient_data['last_updated'],
            patient_data['risk_level'], patient_data['preferred_therapy_mode'],
            patient_data['notes']
        ))
        
        click.echo(f"✅ Patient created successfully! ID: {patient_id}")
        log_action(f"New patient created: {name}", "patient_management", patient_id=patient_id)
        
    except Exception as e:
        click.echo(f"❌ Error creating patient: {e}")

def timedelta(days):
    raise NotImplementedError


@patient.command('list')
@click.option('--active-only', is_flag=True, help='Show only active patients')
@click.option('--limit', default=20, help='Maximum number of patients to show')
def list_patients(active_only, limit):
    """List all patients"""
    try:
        query = "SELECT * FROM patients"
        params = []
        
        if active_only:
            # Active means updated within last 30 days
            cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
            query += " WHERE last_updated > ?"
            params.append(cutoff_date)
        
        query += " ORDER BY last_updated DESC LIMIT ?"
        params.append(limit)
        
        patients = cli.db.execute_query(query, params)
        
        if not patients:
            click.echo("No patients found.")
            return
        
        # Prepare table data
        table_data = []
        for patient in patients:
            # Calculate age
            try:
                birth_date = datetime.fromisoformat(patient['date_of_birth']).date()
                age = (date.today() - birth_date).days // 365
            except:
                age = "Unknown"
            
            table_data.append([
                patient['id'],
                patient['name'],
                age,
                patient['gender'],
                patient['preferred_therapy_mode'],
                patient['risk_level'],
                format_datetime(patient['last_updated'], 'date_only')
            ])
        
        headers = ['ID', 'Name', 'Age', 'Gender', 'Therapy Mode', 'Risk Level', 'Last Updated']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
        click.echo(f"\nShowing {len(patients)} patients")
        
    except Exception as e:
        click.echo(f"❌ Error listing patients: {e}")


@patient.command('view')
@click.argument('patient_id', type=int)
def view_patient(patient_id):
    """View detailed patient information"""
    try:
        # Get patient info
        patient_data = cli.db.execute_query("SELECT * FROM patients WHERE id = ?", (patient_id,))
        if not patient_data:
            click.echo(f"❌ Patient {patient_id} not found.")
            return
        
        patient = patient_data[0]
        
        # Display patient information
        click.echo(f"\n👤 Patient Profile - {patient['name']}")
        click.echo("=" * 50)
        click.echo(f"ID: {patient['id']}")
        click.echo(f"Date of Birth: {patient['date_of_birth']}")
        click.echo(f"Gender: {patient['gender']}")
        click.echo(f"Contact: {patient['contact_info'] or 'Not provided'}")
        click.echo(f"Emergency Contact: {patient['emergency_contact'] or 'Not provided'}")
        click.echo(f"Risk Level: {patient['risk_level']}")
        click.echo(f"Preferred Therapy: {patient['preferred_therapy_mode']}")
        click.echo(f"Created: {format_datetime(patient['created_date'], 'friendly')}")
        click.echo(f"Last Updated: {format_datetime(patient['last_updated'], 'friendly')}")
        
        if patient['notes']:
            click.echo(f"Notes: {patient['notes']}")
        
        # Get session summary
        sessions = cli.db.execute_query(
            "SELECT COUNT(*) as total, MAX(session_date) as last_session FROM sessions WHERE patient_id = ?",
            (patient_id,)
        )
        
        if sessions and sessions[0]['total'] > 0:
            click.echo(f"\n📊 Session Summary:")
            click.echo(f"Total Sessions: {sessions[0]['total']}")
            click.echo(f"Last Session: {format_datetime(sessions[0]['last_session'], 'friendly')}")
        else:
            click.echo(f"\n📊 No sessions recorded yet")
        
        # Get recent assessments
        assessments = cli.db.execute_query(
            "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date DESC LIMIT 3",
            (patient_id,)
        )
        
        if assessments:
            click.echo(f"\n📋 Recent Assessments:")
            for assessment in assessments:
                click.echo(f"• {assessment['assessment_type']}: {assessment['total_score']} ({assessment['severity_level']}) - {format_datetime(assessment['assessment_date'], 'date_only')}")
        
    except Exception as e:
        click.echo(f"❌ Error viewing patient: {e}")


@main.group()
def session():
    """Session management commands"""
    cli.check_initialization()


@session.command('start')
@click.argument('patient_id', type=int)
@click.option('--modality', type=click.Choice(['CBT', 'DBT', 'ACT', 'Psychodynamic']), 
              help='Therapy modality for this session')
def start_session(patient_id, modality):
    """Start a new therapy session"""
    try:
        # Verify patient exists
        patient_data = cli.db.execute_query("SELECT * FROM patients WHERE id = ?", (patient_id,))
        if not patient_data:
            click.echo(f"❌ Patient {patient_id} not found.")
            return
        
        patient = patient_data[0]
        
        # Use patient's preferred modality if not specified
        if not modality:
            modality = patient['preferred_therapy_mode']
        
        click.echo(f"🔄 Starting {modality} session for {patient['name']}...")
        
        # Start session
        result = asyncio.run(cli.session_manager.start_session(patient_id, modality))
        
        click.echo(f"✅ Session started successfully!")
        click.echo(f"Session ID: {result['session_id']}")
        click.echo(f"Therapy Modality: {result['therapy_modality']}")
        click.echo(f"\n💬 AI Therapist: {result['response']}")
        
        # Enter interactive session mode
        click.echo(f"\n🔹 Interactive session mode. Type 'quit' to end session.")
        click.echo(f"🔹 Type 'help' for session commands.")
        
        while True:
            user_input = click.prompt(f"\n{patient['name']}", default="", show_default=False)
            
            if user_input.lower() in ['quit', 'exit', 'end']:
                # End session
                end_result = asyncio.run(cli.session_manager.end_session(patient_id))
                click.echo(f"\n✅ Session ended. Duration: {end_result['session_duration']}")
                break
            
            elif user_input.lower() == 'help':
                click.echo(f"\n📋 Session Commands:")
                click.echo(f"• 'quit' or 'exit' - End the session")
                click.echo(f"• 'status' - Show session status")
                click.echo(f"• 'mood [1-10]' - Rate current mood")
                click.echo(f"• 'crisis' - Trigger crisis intervention")
                continue
            
            elif user_input.lower() == 'status':
                status = cli.session_manager.get_session_status(patient_id)
                click.echo(f"\n📊 Session Status:")
                click.echo(f"Current Phase: {status['current_phase']}")
                click.echo(f"Duration: {status['duration_minutes']} minutes")
                click.echo(f"Engagement Level: {status['engagement_level']}/10")
                continue
            
            elif user_input.lower().startswith('mood '):
                try:
                    mood_rating = int(user_input.split()[1])
                    if 1 <= mood_rating <= 10:
                        # Record mood rating
                        log_action(f"Mood rating recorded: {mood_rating}", "session", patient_id=patient_id)
                        click.echo(f"✅ Mood rating recorded: {mood_rating}/10")
                    else:
                        click.echo("❌ Mood rating must be between 1 and 10")
                except:
                    click.echo("❌ Invalid mood rating format. Use: mood [1-10]")
                continue
            
            elif user_input.lower() == 'crisis':
                click.echo("🚨 Activating crisis intervention protocols...")
                # This would trigger crisis intervention
                continue
            
            if not user_input.strip():
                continue
            
            # Process user input through session manager
            try:
                response = asyncio.run(cli.session_manager.process_user_input(patient_id, user_input))
                
                click.echo(f"\n💬 AI Therapist: {response['response']}")
                
                # Show session progress
                if response.get('next_phase_available'):
                    click.echo(f"🔹 Ready to move to next phase: {response.get('current_phase')}")
                
                # Handle crisis detection
                if response.get('crisis_detected'):
                    click.echo(f"🚨 CRISIS DETECTED - Please ensure patient safety")
                
            except Exception as e:
                click.echo(f"❌ Error processing input: {e}")
        
    except Exception as e:
        click.echo(f"❌ Error starting session: {e}")


@session.command('list')
@click.option('--patient-id', type=int, help='Filter by patient ID')
@click.option('--limit', default=10, help='Maximum number of sessions to show')
def list_sessions(patient_id, limit):
    """List recent sessions"""
    try:
        query = """
        SELECT s.*, p.name as patient_name 
        FROM sessions s 
        JOIN patients p ON s.patient_id = p.id
        """
        params = []
        
        if patient_id:
            query += " WHERE s.patient_id = ?"
            params.append(patient_id)
        
        query += " ORDER BY s.session_date DESC LIMIT ?"
        params.append(limit)
        
        sessions = cli.db.execute_query(query, params)
        
        if not sessions:
            click.echo("No sessions found.")
            return
        
        # Prepare table data
        table_data = []
        for session in sessions:
            table_data.append([
                session['id'],
                session['patient_name'],
                session['session_type'],
                format_datetime(session['session_date'], 'short'),
                f"{session['duration']}m" if session['duration'] else "N/A",
                "✅" if session.get('completed') else "🔄",
                session.get('mood_before', 'N/A'),
                session.get('mood_after', 'N/A')
            ])
        
        headers = ['ID', 'Patient', 'Type', 'Date', 'Duration', 'Status', 'Mood Before', 'Mood After']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
        click.echo(f"\nShowing {len(sessions)} sessions")
        
    except Exception as e:
        click.echo(f"❌ Error listing sessions: {e}")


@main.group()
def assessment():
    """Assessment and evaluation commands"""
    cli.check_initialization()


@assessment.command('run')
@click.argument('patient_id', type=int)
@click.option('--type', 'assessment_type', 
              type=click.Choice(['PHQ9', 'GAD7', 'PCL5', 'ORS', 'SRS']),
              prompt='Assessment type')
def run_assessment(patient_id, assessment_type):
    """Run an assessment for a patient"""
    try:
        # Verify patient exists
        patient_data = cli.db.execute_query("SELECT * FROM patients WHERE id = ?", (patient_id,))
        if not patient_data:
            click.echo(f"❌ Patient {patient_id} not found.")
            return
        
        patient = patient_data[0]
        click.echo(f"📋 Running {assessment_type} assessment for {patient['name']}")
        
        # Get assessment questions
        assessment_data = cli.assessment_system.get_assessment(assessment_type)
        
        if not assessment_data:
            click.echo(f"❌ Assessment {assessment_type} not available.")
            return
        
        click.echo(f"\n{assessment_data['name']}")
        click.echo(f"Description: {assessment_data['description']}")
        click.echo(f"Instructions: {assessment_data['instructions']}")
        click.echo("\nPlease answer each question honestly based on how you've been feeling recently.\n")
        
        responses = {}
        
        # Administer questions
        for i, question in enumerate(assessment_data['questions'], 1):
            click.echo(f"Question {i}: {question['text']}")
            
            # Show response options
            for j, option in enumerate(question['options']):
                click.echo(f"  {j}. {option}")
            
            while True:
                try:
                    response = click.prompt("Your answer (number)", type=int)
                    if 0 <= response < len(question['options']):
                        responses[f"question_{i}"] = {
                            'question': question['text'],
                            'response_index': response,
                            'response_text': question['options'][response],
                            'score': question['scores'][response]
                        }
                        break
                    else:
                        click.echo(f"Please enter a number between 0 and {len(question['options'])-1}")
                except:
                    click.echo("Please enter a valid number")
        
        # Score assessment
        total_score = sum(r['score'] for r in responses.values())
        severity = cli.assessment_system.calculate_severity(assessment_type, total_score)
        interpretation = cli.assessment_system.get_interpretation(assessment_type, total_score)
        
        # Save assessment
        assessment_id = cli.assessment_system.save_assessment(
            patient_id=patient_id,
            assessment_type=assessment_type,
            responses=responses,
            total_score=total_score,
            severity_level=severity,
            interpretation=interpretation
        )
        
        # Show results
        click.echo(f"\n📊 Assessment Results:")
        click.echo(f"Total Score: {total_score}")
        click.echo(f"Severity Level: {severity}")
        click.echo(f"Interpretation: {interpretation}")
        click.echo(f"Assessment ID: {assessment_id}")
        
        # Check for risk factors
        if 'suicide' in interpretation.lower() or severity in ['severe', 'high']:
            click.echo(f"\n🚨 WARNING: High risk indicators detected!")
            click.echo(f"Consider immediate clinical intervention and safety planning.")
        
        log_action(f"{assessment_type} assessment completed", "assessment", 
                  patient_id=patient_id, additional_data={'score': total_score, 'severity': severity})
        
    except Exception as e:
        click.echo(f"❌ Error running assessment: {e}")


@assessment.command('history')
@click.argument('patient_id', type=int)
@click.option('--type', 'assessment_type', help='Filter by assessment type')
@click.option('--limit', default=10, help='Maximum number of assessments to show')
def assessment_history(patient_id, assessment_type, limit):
    """View assessment history for a patient"""
    try:
        query = "SELECT * FROM assessments WHERE patient_id = ?"
        params = [patient_id]
        
        if assessment_type:
            query += " AND assessment_type = ?"
            params.append(assessment_type)
        
        query += " ORDER BY assessment_date DESC LIMIT ?"
        params.append(limit)
        
        assessments = cli.db.execute_query(query, params)
        
        if not assessments:
            click.echo("No assessments found.")
            return
        
        # Prepare table data
        table_data = []
        for assessment in assessments:
            table_data.append([
                assessment['id'],
                assessment['assessment_type'],
                assessment['total_score'],
                assessment['severity_level'],
                format_datetime(assessment['assessment_date'], 'date_only')
            ])
        
        headers = ['ID', 'Type', 'Score', 'Severity', 'Date']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
        click.echo(f"\nShowing {len(assessments)} assessments")
        
    except Exception as e:
        click.echo(f"❌ Error viewing assessment history: {e}")


@main.group()
def admin():
    """Administrative functions"""
    cli.check_initialization()


@admin.command('status')
def system_status():
    """Show system status and health"""
    try:
        health = monitor_system_health()
        
        click.echo(f"🏥 System Health Report")
        click.echo("=" * 40)
        click.echo(f"Overall Status: {health['status'].upper()}")
        click.echo(f"Timestamp: {format_datetime(health['timestamp'], 'friendly')}")
        
        # Show detailed checks
        click.echo(f"\n🔍 System Checks:")
        for check_name, check_data in health['checks'].items():
            status_icon = "✅" if check_data['status'] == 'ok' else "❌"
            click.echo(f"{status_icon} {check_name.replace('_', ' ').title()}: {check_data['status']}")
            
            if 'size_mb' in check_data:
                click.echo(f"   Size: {check_data['size_mb']} MB")
            if 'free_gb' in check_data:
                click.echo(f"   Free Space: {check_data['free_gb']} GB ({check_data['free_percent']}%)")
        
        # Show warnings and errors
        if health['warnings']:
            click.echo(f"\n⚠️  Warnings ({len(health['warnings'])}):")
            for warning in health['warnings']:
                click.echo(f"   • {warning}")
        
        if health['errors']:
            click.echo(f"\n❌ Errors ({len(health['errors'])}):")
            for error in health['errors']:
                click.echo(f"   • {error}")
        
        # Database statistics
        try:
            stats = cli.db.get_database_stats()
            click.echo(f"\n📊 Database Statistics:")
            click.echo(f"   Patients: {stats.get('patient_count', 0)}")
            click.echo(f"   Sessions: {stats.get('session_count', 0)}")
            click.echo(f"   Assessments: {stats.get('assessment_count', 0)}")
            click.echo(f"   Database Size: {stats.get('file_size_mb', 0)} MB")
        except:
            pass
        
    except Exception as e:
        click.echo(f"❌ Error getting system status: {e}")


@admin.command('backup')
@click.option('--description', help='Description for this backup')
def create_backup(description):
    """Create system backup"""
    try:
        click.echo("🔄 Creating system backup...")
        
        backup_file = create_system_backup()
        
        click.echo(f"✅ Backup created successfully!")
        click.echo(f"Backup file: {backup_file}")
        
        if description:
            # Could save backup description to metadata
            log_action(f"Manual backup created: {description}", "admin")
        
    except Exception as e:
        click.echo(f"❌ Error creating backup: {e}")


@admin.command('export')
@click.argument('patient_id', type=int)
@click.option('--format', 'export_format', type=click.Choice(['json', 'csv']), default='json')
def export_patient(patient_id, export_format):
    """Export patient data"""
    try:
        click.echo(f"🔄 Exporting patient {patient_id} data in {export_format.upper()} format...")
        
        export_file = export_patient_data(patient_id, export_format)
        
        click.echo(f"✅ Patient data exported successfully!")
        click.echo(f"Export file: {export_file}")
        
    except Exception as e:
        click.echo(f"❌ Error exporting patient data: {e}")


@admin.command('report')
@click.option('--save', is_flag=True, help='Save report to file')
def system_report(save):
    """Generate system usage report"""
    try:
        click.echo("🔄 Generating system report...")
        
        report = generate_system_report()
        
        # Display report
        click.echo(f"\n📊 System Usage Report")
        click.echo("=" * 50)
        click.echo(f"Generated: {format_datetime(report['generated_at'], 'friendly')}")
        
        click.echo(f"\n👥 Patient Statistics:")
        patient_stats = report['patient_stats']
        click.echo(f"   Total Patients: {patient_stats['total_patients']}")
        click.echo(f"   Active Patients (30 days): {patient_stats['active_patients_30_days']}")
        click.echo(f"   Activity Rate: {patient_stats['patient_activity_rate']}%")
        
        click.echo(f"\n💬 Session Statistics:")
        session_stats = report['session_stats']
        click.echo(f"   Total Sessions: {session_stats['total_sessions']}")
        click.echo(f"   Sessions (last week): {session_stats['sessions_last_week']}")
        click.echo(f"   Avg Sessions/Patient: {session_stats['avg_sessions_per_patient']}")
        
        click.echo(f"\n📋 Assessment Statistics:")
        assessment_stats = report['assessment_stats']
        click.echo(f"   Total Assessments: {assessment_stats['total_assessments']}")
        click.echo(f"  Avg Assessments/Patient: {assessment_stats['avg_assessments_per_patient']}")
        
        click.echo(f"\n🏥 System Health:")
        health = report['system_health']
        click.echo(f"   Status: {health['status'].upper()}")
        click.echo(f"   Warnings: {len(health.get('warnings', []))}")
        click.echo(f"   Errors: {len(health.get('errors', []))}")
        
        if save:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = f"system_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            click.echo(f"\n💾 Report saved to: {report_file}")
        
    except Exception as e:
        click.echo(f"❌ Error generating report: {e}")


@main.group()
def goal():
    """Goal management commands"""
    cli.check_initialization()


@goal.command('create')
@click.argument('patient_id', type=int)
@click.option('--type', 'goal_type', 
              type=click.Choice(['symptom', 'functional', 'behavioral']),
              prompt='Goal type')
@click.option('--description', prompt='Goal description', help='Description of the goal')
@click.option('--target-date', prompt='Target date (YYYY-MM-DD)', help='Target completion date')
@click.option('--criteria', prompt='Measurement criteria', help='How to measure success')
def create_goal(patient_id, goal_type, description, target_date, criteria):
    """Create a new treatment goal"""
    try:
        # Verify patient exists
        patient_data = cli.db.execute_query("SELECT * FROM patients WHERE id = ?", (patient_id,))
        if not patient_data:
            click.echo(f"❌ Patient {patient_id} not found.")
            return
        
        patient = patient_data[0]
        
        # Create goal
        goal_id = cli.goal_manager.create_goal(
            patient_id=patient_id,
            goal_type=goal_type,
            description=description,
            target_date=target_date,
            measurement_criteria=criteria
        )
        
        click.echo(f"✅ Goal created successfully!")
        click.echo(f"Goal ID: {goal_id}")
        click.echo(f"Patient: {patient['name']}")
        click.echo(f"Type: {goal_type}")
        click.echo(f"Description: {description}")
        click.echo(f"Target Date: {target_date}")
        
        log_action(f"New goal created: {description}", "goal_management", patient_id=patient_id)
        
    except Exception as e:
        click.echo(f"❌ Error creating goal: {e}")


@goal.command('list')
@click.argument('patient_id', type=int)
@click.option('--status', type=click.Choice(['active', 'achieved', 'modified', 'discontinued']),
              help='Filter by goal status')
def list_goals(patient_id, status):
    """List goals for a patient"""
    try:
        query = "SELECT * FROM treatment_goals WHERE patient_id = ?"
        params = [patient_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_date DESC"
        
        goals = cli.db.execute_query(query, params)
        
        if not goals:
            click.echo("No goals found.")
            return
        
        # Prepare table data
        table_data = []
        for goal in goals:
            table_data.append([
                goal['id'],
                goal['goal_type'],
                goal['goal_description'][:50] + "..." if len(goal['goal_description']) > 50 else goal['goal_description'],
                f"{goal['current_progress']}%",
                goal['status'],
                format_datetime(goal['target_date'], 'date_only')
            ])
        
        headers = ['ID', 'Type', 'Description', 'Progress', 'Status', 'Target Date']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
        click.echo(f"\nShowing {len(goals)} goals")
        
    except Exception as e:
        click.echo(f"❌ Error listing goals: {e}")


@goal.command('update')
@click.argument('goal_id', type=int)
@click.option('--progress', type=int, help='Progress percentage (0-100)')
@click.option('--status', type=click.Choice(['active', 'achieved', 'modified', 'discontinued']),
              help='Goal status')
@click.option('--notes', help='Progress notes')
def update_goal(goal_id, progress, status, notes):
    """Update goal progress"""
    try:
        # Get current goal
        goal_data = cli.db.execute_query("SELECT * FROM treatment_goals WHERE id = ?", (goal_id,))
        if not goal_data:
            click.echo(f"❌ Goal {goal_id} not found.")
            return
        
        goal = goal_data[0]
        
        # Update goal
        update_data = {}
        if progress is not None:
            if 0 <= progress <= 100:
                update_data['current_progress'] = progress
            else:
                click.echo("❌ Progress must be between 0 and 100")
                return
        
        if status:
            update_data['status'] = status
        
        if notes:
            # Append to existing notes
            existing_notes = goal.get('notes', '') or ''
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            new_notes = f"{existing_notes}\n[{timestamp}] {notes}".strip()
            update_data['notes'] = new_notes
        
        if update_data:
            update_data['last_updated'] = datetime.now().isoformat()
            
            # Build update query
            set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
            query = f"UPDATE treatment_goals SET {set_clause} WHERE id = ?"
            params = list(update_data.values()) + [goal_id]
            
            cli.db.execute_update(query, params)
            
            click.echo(f"✅ Goal updated successfully!")
            
            if progress is not None:
                click.echo(f"Progress: {progress}%")
                if progress == 100:
                    click.echo("🎉 Goal completed! Consider setting as 'achieved' status.")
            
            if status:
                click.echo(f"Status: {status}")
            
            log_action(f"Goal updated: {goal['goal_description'][:50]}", "goal_management", 
                      patient_id=goal['patient_id'], additional_data=update_data)
        else:
            click.echo("No updates specified.")
        
    except Exception as e:
        click.echo(f"❌ Error updating goal: {e}")


@main.group()
def homework():
    """Homework assignment commands"""
    cli.check_initialization()


@homework.command('assign')
@click.argument('patient_id', type=int)
@click.argument('session_id', type=int)
@click.option('--type', 'assignment_type', 
              type=click.Choice(['thought_record', 'activity_log', 'exposure', 'mindfulness', 'skills_practice']),
              prompt='Assignment type')
@click.option('--description', prompt='Assignment description', help='What the patient should do')
@click.option('--instructions', help='Detailed instructions')
@click.option('--due-days', type=int, default=7, help='Days until due (default: 7)')
def assign_homework(patient_id, session_id, assignment_type, description, instructions, due_days):
    """Assign homework to a patient"""
    try:
        # Verify patient and session exist
        patient_data = cli.db.execute_query("SELECT * FROM patients WHERE id = ?", (patient_id,))
        if not patient_data:
            click.echo(f"❌ Patient {patient_id} not found.")
            return
        
        session_data = cli.db.execute_query("SELECT * FROM sessions WHERE id = ? AND patient_id = ?", 
                                           (session_id, patient_id))
        if not session_data:
            click.echo(f"❌ Session {session_id} not found for patient {patient_id}.")
            return
        
        patient = patient_data[0]
        
        # Calculate due date
        due_date = (datetime.now() + timedelta(days=due_days)).isoformat()
        
        # Create homework assignment
        assignment_id = cli.db.execute_update('''
            INSERT INTO homework_assignments 
            (patient_id, session_id, assignment_type, description, instructions, 
             assigned_date, due_date, completed, completion_notes, effectiveness_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id, session_id, assignment_type, description, instructions or description,
            datetime.now().isoformat(), due_date, False, None, None
        ))
        
        click.echo(f"✅ Homework assigned successfully!")
        click.echo(f"Assignment ID: {assignment_id}")
        click.echo(f"Patient: {patient['name']}")
        click.echo(f"Type: {assignment_type}")
        click.echo(f"Description: {description}")
        click.echo(f"Due Date: {format_datetime(due_date, 'friendly')}")
        
        log_action(f"Homework assigned: {assignment_type}", "homework", 
                  patient_id=patient_id, session_id=session_id)
        
    except Exception as e:
        click.echo(f"❌ Error assigning homework: {e}")


@homework.command('list')
@click.argument('patient_id', type=int)
@click.option('--status', type=click.Choice(['pending', 'completed', 'overdue']),
              help='Filter by completion status')
def list_homework(patient_id, status):
    """List homework assignments for a patient"""
    try:
        query = "SELECT * FROM homework_assignments WHERE patient_id = ?"
        params = [patient_id]
        
        if status == 'pending':
            query += " AND completed = FALSE AND due_date > ?"
            params.append(datetime.now().isoformat())
        elif status == 'completed':
            query += " AND completed = TRUE"
        elif status == 'overdue':
            query += " AND completed = FALSE AND due_date <= ?"
            params.append(datetime.now().isoformat())
        
        query += " ORDER BY due_date DESC"
        
        assignments = cli.db.execute_query(query, params)
        
        if not assignments:
            click.echo("No homework assignments found.")
            return
        
        # Prepare table data
        table_data = []
        for assignment in assignments:
            # Determine status
            if assignment['completed']:
                status_icon = "✅"
                status_text = "Completed"
            elif assignment['due_date'] <= datetime.now().isoformat():
                status_icon = "⏰"
                status_text = "Overdue"
            else:
                status_icon = "📝"
                status_text = "Pending"
            
            table_data.append([
                assignment['id'],
                assignment['assignment_type'],
                assignment['description'][:40] + "..." if len(assignment['description']) > 40 else assignment['description'],
                format_datetime(assignment['due_date'], 'date_only'),
                f"{status_icon} {status_text}",
                assignment['effectiveness_rating'] or "N/A"
            ])
        
        headers = ['ID', 'Type', 'Description', 'Due Date', 'Status', 'Rating']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
        click.echo(f"\nShowing {len(assignments)} assignments")
        
    except Exception as e:
        click.echo(f"❌ Error listing homework: {e}")


@homework.command('complete')
@click.argument('assignment_id', type=int)
@click.option('--notes', prompt='Completion notes', help='How did the assignment go?')
@click.option('--rating', type=int, help='Effectiveness rating (1-5)')
def complete_homework(assignment_id, notes, rating):
    """Mark homework assignment as completed"""
    try:
        # Get assignment
        assignment_data = cli.db.execute_query("SELECT * FROM homework_assignments WHERE id = ?", 
                                              (assignment_id,))
        if not assignment_data:
            click.echo(f"❌ Assignment {assignment_id} not found.")
            return
        
        assignment = assignment_data[0]
        
        if assignment['completed']:
            click.echo(f"⚠️  Assignment already marked as completed.")
            return
        
        # Validate rating if provided
        if rating is not None and not (1 <= rating <= 5):
            click.echo("❌ Rating must be between 1 and 5")
            return
        
        # Mark as completed
        cli.db.execute_update('''
            UPDATE homework_assignments 
            SET completed = TRUE, completion_date = ?, completion_notes = ?, effectiveness_rating = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), notes, rating, assignment_id))
        
        click.echo(f"✅ Homework assignment completed!")
        click.echo(f"Assignment: {assignment['assignment_type']}")
        click.echo(f"Completion notes: {notes}")
        
        if rating:
            click.echo(f"Effectiveness rating: {rating}/5")
        
        log_action(f"Homework completed: {assignment['assignment_type']}", "homework",
                  patient_id=assignment['patient_id'])
        
    except Exception as e:
        click.echo(f"❌ Error completing homework: {e}")


@main.group()
def docs():
    """Documentation and reporting commands"""
    cli.check_initialization()


@docs.command('note')
@click.argument('patient_id', type=int)
@click.argument('session_id', type=int)
@click.option('--type', 'note_type', type=click.Choice(['SOAP', 'progress', 'crisis']), default='progress')
def create_note(patient_id, session_id, note_type):
    """Create a progress note"""
    try:
        # Verify patient and session
        patient_data = cli.db.execute_query("SELECT * FROM patients WHERE id = ?", (patient_id,))
        if not patient_data:
            click.echo(f"❌ Patient {patient_id} not found.")
            return
        
        session_data = cli.db.execute_query("SELECT * FROM sessions WHERE id = ? AND patient_id = ?", 
                                           (session_id, patient_id))
        if not session_data:
            click.echo(f"❌ Session {session_id} not found for patient {patient_id}.")
            return
        
        patient = patient_data[0]
        session = session_data[0]
        
        click.echo(f"📝 Creating {note_type} note for {patient['name']}")
        click.echo(f"Session Date: {format_datetime(session['session_date'], 'friendly')}")
        
        if note_type == 'SOAP':
            click.echo(f"\nSOAP Note Format:")
            subjective = click.prompt("Subjective (patient's report)")
            objective = click.prompt("Objective (observable behaviors)")
            assessment = click.prompt("Assessment (clinical impression)")
            plan = click.prompt("Plan (treatment plan)")
            
            # Create SOAP note
            note_id = cli.db.execute_update('''
                INSERT INTO progress_notes 
                (patient_id, session_id, note_type, subjective, objective, assessment, plan, 
                 created_date, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (patient_id, session_id, note_type, subjective, objective, assessment, plan,
                  datetime.now().isoformat(), "System User"))
            
        else:
            # Simple progress note
            content = click.prompt("Progress note content")
            
            note_id = cli.db.execute_update('''
                INSERT INTO progress_notes 
                (patient_id, session_id, note_type, subjective, objective, assessment, plan,
                 created_date, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (patient_id, session_id, note_type, content, "", "", "",
                  datetime.now().isoformat(), "System User"))
        
        click.echo(f"✅ Progress note created successfully!")
        click.echo(f"Note ID: {note_id}")
        
        log_action(f"{note_type} note created", "documentation", 
                  patient_id=patient_id, session_id=session_id)
        
    except Exception as e:
        click.echo(f"❌ Error creating note: {e}")


@docs.command('view')
@click.argument('patient_id', type=int)
@click.option('--limit', default=5, help='Number of recent notes to show')
def view_notes(patient_id, limit):
    """View recent progress notes for a patient"""
    try:
        notes = cli.db.execute_query('''
            SELECT pn.*, s.session_date 
            FROM progress_notes pn
            JOIN sessions s ON pn.session_id = s.id
            WHERE pn.patient_id = ?
            ORDER BY pn.created_date DESC
            LIMIT ?
        ''', (patient_id, limit))
        
        if not notes:
            click.echo("No progress notes found.")
            return
        
        patient_data = cli.db.execute_query("SELECT name FROM patients WHERE id = ?", (patient_id,))
        patient_name = patient_data[0]['name'] if patient_data else f"Patient {patient_id}"
        
        click.echo(f"📋 Progress Notes for {patient_name}")
        click.echo("=" * 60)
        
        for note in notes:
            click.echo(f"\nNote ID: {note['id']} | Type: {note['note_type']} | Session: {format_datetime(note['session_date'], 'date_only')}")
            click.echo(f"Created: {format_datetime(note['created_date'], 'friendly')} by {note['created_by']}")
            click.echo("-" * 40)
            
            if note['note_type'] == 'SOAP':
                click.echo(f"S: {note['subjective']}")
                click.echo(f"O: {note['objective']}")
                click.echo(f"A: {note['assessment']}")
                click.echo(f"P: {note['plan']}")
            else:
                click.echo(f"Content: {note['subjective']}")
        
    except Exception as e:
        click.echo(f"❌ Error viewing notes: {e}")


@main.command()
@click.option('--port', default=8000, help='Port for web interface')
@click.option('--host', default='localhost', help='Host for web interface')
def web(port, host):
    """Launch web interface (future feature)"""
    click.echo(f"🌐 Web interface not yet implemented")
    click.echo(f"   This feature will launch a web-based interface at http://{host}:{port}")
    click.echo(f"   For now, please use the CLI interface")


@main.command()
def version():
    """Show version information"""
    click.echo(f"AI Therapy System MVP v1.0.0")
    click.echo(f"Built with Gemini 2.5 Pro integration")
    click.echo(f"Supporting CBT, DBT, ACT, and Psychodynamic therapy modalities")


# Global exception handler
def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Handle Ctrl+C gracefully
        click.echo(f"\n\n🛑 Operation cancelled by user")
        cli.shutdown_system()
        sys.exit(0)
    
    # Log the exception
    if cli.logger:
        cli.logger.error(f"Unhandled exception: {exc_type.__name__}: {exc_value}", 
                        exc_info=(exc_type, exc_value, exc_traceback))
    
    # Show user-friendly error message
    click.echo(f"\n❌ An unexpected error occurred: {exc_value}")
    click.echo(f"   Error type: {exc_type.__name__}")
    click.echo(f"   Check logs for more details")
    
    # Attempt graceful shutdown
    try:
        cli.shutdown_system()
    except:
        pass


# Setup global exception handling
sys.excepthook = handle_exception


def validate_environment():
    """Validate environment before starting"""
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append("Python 3.8 or higher required")
    
    # Check for Gemini API key
    #if not os.getenv('GEMINI_API_KEY'):
    #    issues.append("GEMINI_API_KEY environment variable not set")
    
    # Check write permissions
    try:
        test_file = '.write_test'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except:
        issues.append("No write permission in current directory")
    
    return issues


if __name__ == '__main__':
    # Validate environment before starting
    env_issues = validate_environment()
    if env_issues:
        click.echo(f"❌ Environment issues detected:")
        for issue in env_issues:
            click.echo(f"   • {issue}")
        click.echo(f"\nPlease resolve these issues before running the system.")
        sys.exit(1)
    
    # Register cleanup on exit
    import atexit
    atexit.register(cli.shutdown_system)
    
    # Start the CLI
    try:
        main()
    except KeyboardInterrupt:
        click.echo(f"\n\n🛑 System shutdown requested")
        cli.shutdown_system()
    except Exception as e:
        click.echo(f"\n❌ Critical error: {e}")
        if cli.logger:
            cli.logger.critical(f"Critical startup error: {e}")
        sys.exit(1)
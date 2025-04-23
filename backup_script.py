import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sqlite3
import subprocess
import time
from dotenv import load_dotenv
import shutil

# Load environment variables
load_dotenv()

# Configuration
DATABASE_PATHS = [
    '/path/to/your/database.sqlite3',  # Add your SQLite database path
    '/path/to/your/database.sql'       # Add your SQL database path if needed
]
BACKUP_DIR = 'backups'
EMAIL_SENDER = os.getenv('tai123409876@gmail.com')
EMAIL_PASSWORD = os.getenv('avrk qmvg gcvu fvca')
EMAIL_RECEIVER = os.getenv('tai_2251220183@dau.edu.vn')
SMTP_SERVER = 'smtp.gmail.com'  # Change if using different provider
SMTP_PORT = 587

def create_backup_dir():
    """Create backup directory if it doesn't exist"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

def backup_sqlite(db_path):
    """Backup SQLite database"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{os.path.basename(db_path)}_{timestamp}.bak"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        
        # Create backup
        with open(backup_path, 'w') as f:
            for line in conn.iterdump():
                f.write('%s\n' % line)
        
        conn.close()
        return True, backup_path
    except Exception as e:
        return False, str(e)

def backup_mysql(db_path):
    """Backup MySQL database (if using .sql files)"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{os.path.basename(db_path)}_{timestamp}.bak"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # For MySQL, you would typically use mysqldump
        # This is a placeholder - adjust for your MySQL setup
        shutil.copy2(db_path, backup_path)
        return True, backup_path
    except Exception as e:
        return False, str(e)

def send_email(subject, body):
    """Send email notification"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def perform_backup():
    """Perform backup of all databases"""
    create_backup_dir()
    results = []
    
    for db_path in DATABASE_PATHS:
        if not os.path.exists(db_path):
            results.append((db_path, False, f"Database file not found: {db_path}"))
            continue
            
        if db_path.endswith('.sqlite3'):
            success, result = backup_sqlite(db_path)
        elif db_path.endswith('.sql'):
            success, result = backup_mysql(db_path)
        else:
            success, result = False, f"Unsupported database format: {db_path}"
            
        results.append((db_path, success, result))
    
    return results

def generate_report(results):
    """Generate backup report"""
    success_count = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    report = f"Database Backup Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"Success: {success_count}/{total}\n\n"
    
    for db_path, success, result in results:
        status = "SUCCESS" if success else "FAILED"
        report += f"Database: {db_path}\n"
        report += f"Status: {status}\n"
        if success:
            report += f"Backup saved to: {result}\n"
        else:
            report += f"Error: {result}\n"
        report += "\n"
    
    return report

def main():
    # Wait until midnight
    print("Database backup service started. Waiting until midnight...")
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            print("Midnight detected. Starting backup process...")
            results = perform_backup()
            report = generate_report(results)
            
            # Send email notification
            subject = "Database Backup Report"
            if all(success for _, success, _ in results):
                subject += " - SUCCESS"
            else:
                subject += " - FAILED"
            
            email_sent = send_email(subject, report)
            
            if email_sent:
                print("Email notification sent successfully")
            else:
                print("Failed to send email notification")
            
            print("Backup process completed. Waiting until next midnight...")
            
            # Sleep for 1 hour to avoid multiple executions at midnight
            time.sleep(3600)
        else:
            # Check every minute
            time.sleep(60)

if __name__ == "__main__":
    main()
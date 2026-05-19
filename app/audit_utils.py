from flask import app, request
from .data import sa_db, AuditLog
from datetime import datetime
from flask_login import user_logged_in, user_logged_out


def log_audit(user_id, action, audit_metadata=None, ip_address=None):
    try:
        if ip_address is None:
            ip_address = request.remote_addr or '0.0.0.0'
        
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            audit_metadata=audit_metadata or {},
            ip_address=ip_address,
            timestamp=datetime.now().isoformat()
        )
        
        sa_db.session.add(audit_log)
        sa_db.session.commit()
    except Exception as e:
        sa_db.session.rollback()
        print(f"Error logging audit: {str(e)}")
        
        
def register_audit_signals(app): 
    @user_logged_in.connect_via(app)
    def log_login(sender, user, **extra):
        log_audit(
            user_id=user.id,
            action='login',
            audit_metadata={'email': user.email}
        )

    @user_logged_out.connect_via(app)
    def log_logout(sender, user, **extra):
        log_audit(
            user_id=user.id,
            action='logout',
            audit_metadata={'email': user.email}
        )

from flask import request
from .data import sa_db, AuditLog
from datetime import datetime


def log_audit(user_id, action, audit_metadata=None, ip_address=None):
    """
    Registra una acción de auditoría en la base de datos.
    
    Args:
        user_id: ID del usuario (puede ser None para fallos de login)
        action: Tipo de acción (login, logout, etc.)
        audit_metadata: Diccionario con información adicional
        ip_address: Dirección IP del cliente
    """
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

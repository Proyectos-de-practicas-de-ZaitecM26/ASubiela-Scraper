import stripe
import app.routes.stripe_pay as stripe_pay
from app.data.models import User, sa_db
from flask import Blueprint, Flask, redirect, current_app, render_template, url_for
from flask_login import current_user

payments_bp = Blueprint("payments", __name__)


@payments_bp.route('/gestion-pagos')
def gestion_pagos():
    """
    Muestra la página con los planes de suscripción para el scraper.
    """
    stripe_customer_id = current_user.stripe_customer_id
    subscription_status = current_user.subscription_status

    if subscription_status == "active" or subscription_status == "trialing":
        is_subscribed = True 
    else:
        is_subscribed = False
    return render_template('pagos.html', is_subscribed=is_subscribed)
    
@payments_bp.route('/success', methods=['GET'])
def success():
    dbUser = User.query.get(current_user.id)
    try:
        dbUser.subscription_status = 'active'
        sa_db.session.commit()
    except Exception as e:
        sa_db.session.rollback()
        current_app.logger.error(f"Error al actualizar el estado de suscripción: {e}")
    return render_template('success.html')
    
@payments_bp.route('/cancel', methods=['GET'])
def cancel():
    return render_template('cancel.html')
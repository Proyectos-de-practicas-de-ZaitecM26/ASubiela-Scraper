import stripe
from flask import Blueprint, Flask, redirect, current_app, render_template, url_for

stripe_pay_bp = Blueprint("stripe_pay", __name__, url_prefix='/stripe')


@stripe_pay_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': 'price_1TgNBCEPPkYDpAwIIr5BCdCc', 
                'quantity': 1,
            }],
            mode='subscription', # o 'payment' para pago único
            success_url=url_for('payments.success', _external=True),
            cancel_url=url_for('payments.cancel', _external=True),
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return str(e)
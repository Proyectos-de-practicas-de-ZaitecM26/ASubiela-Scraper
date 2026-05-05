from flask_mail import Mail
from flask_login import LoginManager

mail = Mail()
login_manager = LoginManager()

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[]
)
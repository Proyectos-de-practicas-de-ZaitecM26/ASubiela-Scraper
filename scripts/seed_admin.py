import os
import argparse
from getpass import getpass
from werkzeug.security import generate_password_hash

from app import create_app
from app.data import sa_db, User


def create_admin(app, email, password, name="Admin"):
    with app.app_context():
      # sa_db.init_app(app)
        sa_db.create_all()
        email = email.lower().strip()
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = generate_password_hash(password)
            user.role = 'admin'
            print(f"Actualizado usuario existente {email} como admin.")
        else:
            user = User(email=email, password_hash=generate_password_hash(password), name=name, role='admin')
            sa_db.session.add(user)
            print(f"Creado usuario admin {email}.")
        sa_db.session.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crear/sementar administrador inicial')
    parser.add_argument('--email', help='Email del admin (o env SEED_ADMIN_EMAIL)')
    parser.add_argument('--password', help='Contraseña del admin (o env SEED_ADMIN_PASSWORD)')
    parser.add_argument('--non-interactive', action='store_true', help='No preguntar, usar variables de entorno')
    args = parser.parse_args()

    email = args.email or os.getenv('SEED_ADMIN_EMAIL')
    password = args.password or os.getenv('SEED_ADMIN_PASSWORD')

    if not args.non_interactive:
        if not email:
            email = input('Email admin: ').strip()
        if not password:
            password = getpass('Contraseña admin: ')

    if not email or not password:
        print('Faltan email o contraseña. Use --non-interactive o defina variables de entorno.')
        raise SystemExit(1)

    app = create_app()
    create_admin(app, email, password)

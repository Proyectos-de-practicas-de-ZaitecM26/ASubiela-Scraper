from app import create_app
from app.data import sa_db, User
from app.routes.auth import create_user


def make_app():
    # Pass overrides so DB is configured before extensions init
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    return app


def test_create_user_assigns_viewer():
    app = make_app()
    with app.app_context():
        # `create_app()` already initializes `sa_db` in this project flow; just create tables
        sa_db.create_all()
        u = create_user('permtest@example.com', 'secret123', 'Perm', 'Tester', 30)
        assert u is not None
        assert getattr(u, 'role', None) == 'viewer'


def test_role_column_default_exists():
    app = make_app()
    with app.app_context():
        # `create_app()` already initializes `sa_db` in this project flow; just create tables
        sa_db.create_all()
        # create a user directly via model
        u = User(email='u2@example.com', password_hash='x', name='X', apellidos='Y', age=20)
        sa_db.session.add(u)
        sa_db.session.commit()
        found = User.query.filter_by(email='u2@example.com').first()
        assert found is not None
        assert getattr(found, 'role', None) == 'viewer'

from app import app, db
from app.models import Role, User

with app.app_context():
    db.create_all()

    # Create initial roles
    if not Role.query.filter_by(name='admin').first():
        admin_role = Role(name='admin', description='Administrator role')
        db.session.add(admin_role)
    if not Role.query.filter_by(name='mechanic').first():
        mechanic_role = Role(name='mechanic', description='Mechanic role')
        db.session.add(mechanic_role)
    if not Role.query.filter_by(name='frontend_user').first():
        frontend_user_role = Role(name='frontend_user', description='Frontend user role')
        db.session.add(frontend_user_role)
    if not Role.query.filter_by(name='backend_user').first():
        backend_user_role = Role(name='backend_user', description='Backend user role')
        db.session.add(backend_user_role)
    if not User.query.filter_by(username="Admin").first():
        admin_user = User(username='Admin', phone_number="0877993946", password="$2b$12$rO6wrQC5uuyOg/LYIUbvmOxd7KhL3qaWfITos07XbCAgREWXlF2Am" )
        db.session.add(admin_user)
    if not User.query.filter_by(username="Mechanic").first():
        mechanic_user = User(username='Mechanic', phone_number="08779939461", password="$2b$12$rO6wrQC5uuyOg/LYIUbvmOxd7KhL3qaWfITos07XbCAgREWXlF2Am" )
        db.session.add(mechanic_user)
    db.session.commit()

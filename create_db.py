from app import app, db
from app.models import Role, User
from flask_bcrypt import Bcrypt
from sqlalchemy import text

bcrypt = Bcrypt(app)

with app.app_context():
    db.create_all()

    # Create initial roles
    roles = {
        'admin': 'Administrator role',
        'mechanic': 'Mechanic role',
        'frontend_user': 'Frontend user role',
        'backend_user': 'Backend user role'
    }

    for role_name, role_description in roles.items():
        if not Role.query.filter_by(name=role_name).first():
            role = Role(name=role_name, description=role_description)
            db.session.add(role)

    db.session.commit()  # Commit roles to the database before adding users

    # Create and assign roles to initial users
    if not User.query.filter_by(username="Admin").first():
        admin_user = User(username='Admin', phone_number="0877993946", password="$2b$12$rO6wrQC5uuyOg/LYIUbvmOxd7KhL3qaWfITos07XbCAgREWXlF2Am", image_file='default.jpg')
        db.session.add(admin_user)
        db.session.commit()  # Commit admin user to get its ID
        admin_role = Role.query.filter_by(name='admin').first()
        admin_user.roles.append(admin_role)
        db.session.commit()  # Commit role assignment

    if not User.query.filter_by(username="РоБот").first():
        mechanic_user = User(username='РоБот', phone_number="08779939461", password="$2b$12$rO6wrQC5uuyOg/LYIUbvmOxd7KhL3qaWfITos07XbCAgREWXlF2Am", image_file='robot.jpg')
        db.session.add(mechanic_user)
        db.session.commit()  # Commit mechanic user to get its ID
        mechanic_role = Role.query.filter_by(name='mechanic').first()
        mechanic_user.roles.append(mechanic_role)
        db.session.commit()  # Commit role assignment

    if not User.query.filter_by(username="Анонимен").first():
        anonymous_user = User(username='Анонимен', phone_number='0000000000', password="$2b$12$rO6wrQC5uuyOg/LYIUbvmOxd7KhL3qaWfITos07XbCAgREWXlF2Am", image_file='default.jpg')
        db.session.add(anonymous_user)
        db.session.commit()  # Commit anonymous user to get its ID
        frontend_user_role = Role.query.filter_by(name='frontend_user').first()
        anonymous_user.roles.append(frontend_user_role)
        db.session.commit()  # Commit role assignment

    # Ensure user_roles table contains the necessary rows
    user_roles_rows = [
        {'user_id': 1, 'role_id': 1},
        {'user_id': 2, 'role_id': 2}
    ]

    for row in user_roles_rows:
        user_role = db.session.execute(
            text("SELECT * FROM user_roles WHERE user_id = :user_id AND role_id = :role_id"),
            {'user_id': row['user_id'], 'role_id': row['role_id']}
        ).fetchone()

        if not user_role:
            db.session.execute(
                text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"),
                {'user_id': row['user_id'], 'role_id': row['role_id']}
            )

    db.session.commit()  # Final commit to ensure everything is saved

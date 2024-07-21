
"""Add image_file to User model

Revision ID: 99fe993daf01
Revises: 4cc87bdd1b8f
Create Date: 2024-07-21 00:01:33.961090

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '99fe993daf01'
down_revision = '4cc87bdd1b8f'
branch_labels = None
depends_on = None


def upgrade():
    # Check if the column already exists before adding it
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    columns = [column['name'] for column in inspector.get_columns('user')]
    if 'image_file' not in columns:
        op.add_column('user', sa.Column('image_file', sa.String(length=20), nullable=False, server_default='default.jpg'))


def downgrade():
    op.drop_column('user', 'image_file')
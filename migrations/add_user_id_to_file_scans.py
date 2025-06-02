"""Add user_id to file_scans table

Revision ID: add_user_id_to_file_scans
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add user_id column
    op.add_column('file_scans', sa.Column('user_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_file_scans_user_id_users',
        'file_scans', 'users',
        ['user_id'], ['user_id']
    )
    
    # Make user_id not nullable after adding the constraint
    op.alter_column('file_scans', 'user_id',
                    existing_type=sa.Integer(),
                    nullable=False)

def downgrade():
    # Remove foreign key constraint first
    op.drop_constraint('fk_file_scans_user_id_users', 'file_scans', type_='foreignkey')
    
    # Remove user_id column
    op.drop_column('file_scans', 'user_id') 
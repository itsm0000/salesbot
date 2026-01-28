"""Add operator support - operators table, bot_memories table, operator_id column

Revision ID: 001_add_operator_support
Revises: None (initial migration)
Create Date: 2026-01-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '001_add_operator_support'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add operator support tables and columns"""
    
    # Create operators table
    op.create_table(
        'operators',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('phone', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('password_hash', sa.String(256), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create bot_memories table
    op.create_table(
        'bot_memories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id'), unique=True, nullable=False),
        sa.Column('persona_name', sa.String(100), nullable=True),
        sa.Column('persona_prompt', sa.Text(), nullable=True),
        sa.Column('tone', sa.String(50), default='friendly'),
        sa.Column('permanent_memory', sa.JSON(), nullable=True),
        sa.Column('max_discount_percent', sa.Integer(), default=10),
        sa.Column('shipping_baghdad', sa.Integer(), default=5000),
        sa.Column('shipping_other', sa.Integer(), default=10000),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Add operator_id column to businesses table
    # Using batch mode for SQLite compatibility
    with op.batch_alter_table('businesses') as batch_op:
        batch_op.add_column(
            sa.Column('operator_id', sa.Integer(), sa.ForeignKey('operators.id'), nullable=True)
        )


def downgrade() -> None:
    """Remove operator support"""
    
    # Remove operator_id from businesses
    with op.batch_alter_table('businesses') as batch_op:
        batch_op.drop_column('operator_id')
    
    # Drop tables
    op.drop_table('bot_memories')
    op.drop_table('operators')

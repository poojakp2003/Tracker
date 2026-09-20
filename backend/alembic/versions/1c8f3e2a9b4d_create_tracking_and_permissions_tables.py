"""create tracking and permissions tables

Revision ID: 1c8f3e2a9b4d
Revises: 0b11106d0b6f
Create Date: 2026-09-18 15:40:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c8f3e2a9b4d'
down_revision: str | Sequence[str] | None = '0b11106d0b6f'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('app_tracking', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('browser_tracking', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('youtube_tracking', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_permissions_user_id'), 'permissions', ['user_id'], unique=True)

    # 2. app_usage table
    op.create_table(
        'app_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('app_name', sa.String(length=255), nullable=False),
        sa.Column('window_title', sa.String(length=512), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_app_usage_user_id'), 'app_usage', ['user_id'], unique=False)
    op.create_index(op.f('ix_app_usage_app_name'), 'app_usage', ['app_name'], unique=False)
    op.create_index(op.f('ix_app_usage_start_time'), 'app_usage', ['start_time'], unique=False)
    op.create_index(op.f('ix_app_usage_end_time'), 'app_usage', ['end_time'], unique=False)

    # 3. browser_activity table
    op.create_table(
        'browser_activity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('browser', sa.String(length=100), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('title', sa.String(length=1024), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_browser_activity_user_id'), 'browser_activity', ['user_id'], unique=False)
    op.create_index(op.f('ix_browser_activity_browser'), 'browser_activity', ['browser'], unique=False)
    op.create_index(op.f('ix_browser_activity_timestamp'), 'browser_activity', ['timestamp'], unique=False)

    # 4. youtube_activity table
    op.create_table(
        'youtube_activity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('video_id', sa.String(length=64), nullable=False),
        sa.Column('video_title', sa.String(length=512), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('watched_time_seconds', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_youtube_activity_user_id'), 'youtube_activity', ['user_id'], unique=False)
    op.create_index(op.f('ix_youtube_activity_video_id'), 'youtube_activity', ['video_id'], unique=False)
    op.create_index(op.f('ix_youtube_activity_timestamp'), 'youtube_activity', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_youtube_activity_timestamp'), table_name='youtube_activity')
    op.drop_index(op.f('ix_youtube_activity_video_id'), table_name='youtube_activity')
    op.drop_index(op.f('ix_youtube_activity_user_id'), table_name='youtube_activity')
    op.drop_table('youtube_activity')

    op.drop_index(op.f('ix_browser_activity_timestamp'), table_name='browser_activity')
    op.drop_index(op.f('ix_browser_activity_browser'), table_name='browser_activity')
    op.drop_index(op.f('ix_browser_activity_user_id'), table_name='browser_activity')
    op.drop_table('browser_activity')

    op.drop_index(op.f('ix_app_usage_end_time'), table_name='app_usage')
    op.drop_index(op.f('ix_app_usage_start_time'), table_name='app_usage')
    op.drop_index(op.f('ix_app_usage_app_name'), table_name='app_usage')
    op.drop_index(op.f('ix_app_usage_user_id'), table_name='app_usage')
    op.drop_table('app_usage')

    op.drop_index(op.f('ix_permissions_user_id'), table_name='permissions')
    op.drop_table('permissions')

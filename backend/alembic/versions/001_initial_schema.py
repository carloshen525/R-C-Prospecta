"""Initial database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Settings
    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_settings_key'), 'settings', ['key'], unique=True)
    op.create_index(op.f('ix_settings_id'), 'settings', ['id'], unique=False)

    # Lead Sources
    op.create_table(
        'lead_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lead_sources_slug'), 'lead_sources', ['slug'], unique=True)

    # Campaigns
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('segment', sa.String(length=150), nullable=True),
        sa.Column('location', sa.String(length=150), nullable=True),
        sa.Column('ai_provider', sa.String(length=50), nullable=False),
        sa.Column('ai_model', sa.String(length=100), nullable=False),
        sa.Column('custom_prompt', sa.Text(), nullable=True),
        sa.Column('daily_limit', sa.Integer(), nullable=False, default=30),
        sa.Column('interval_min_seconds', sa.Integer(), nullable=False, default=180),
        sa.Column('interval_max_seconds', sa.Integer(), nullable=False, default=360),
        sa.Column('followup_1_delay_hours', sa.Integer(), nullable=False, default=24),
        sa.Column('followup_2_delay_hours', sa.Integer(), nullable=False, default=48),
        sa.Column('status', sa.String(length=50), nullable=False, default='rascunho'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_campaigns_name'), 'campaigns', ['name'], unique=False)
    op.create_index(op.f('ix_campaigns_status'), 'campaigns', ['status'], unique=False)

    # Extraction Jobs
    op.create_table(
        'extraction_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('segment', sa.String(length=150), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=50), nullable=False),
        sa.Column('country', sa.String(length=50), nullable=False, default='Brasil'),
        sa.Column('desired_qty', sa.Integer(), nullable=False, default=50),
        sa.Column('has_phone_filter', sa.Boolean(), nullable=True, default=True),
        sa.Column('has_website_filter', sa.Boolean(), nullable=True, default=False),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id'), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('found_count', sa.Integer(), default=0),
        sa.Column('processed_count', sa.Integer(), default=0),
        sa.Column('saved_count', sa.Integer(), default=0),
        sa.Column('duplicate_count', sa.Integer(), default=0),
        sa.Column('error_count', sa.Integer(), default=0),
        sa.Column('execution_time_seconds', sa.Float(), default=0.0),
        sa.Column('error_log', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Leads
    op.create_table(
        'leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('raw_phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=50), nullable=True),
        sa.Column('country', sa.String(length=50), nullable=False, default='Brasil'),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=150), nullable=True),
        sa.Column('segment', sa.String(length=150), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('rating_count', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False, default='Google Maps'),
        sa.Column('status', sa.String(length=50), nullable=False, default='novo'),
        sa.Column('is_eligible', sa.Boolean(), nullable=False, default=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('website_analyzed_at', sa.DateTime(), nullable=True),
        sa.Column('website_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leads_phone'), 'leads', ['phone'], unique=False)
    op.create_index(op.f('ix_leads_company_name'), 'leads', ['company_name'], unique=False)
    op.create_index(op.f('ix_leads_status'), 'leads', ['status'], unique=False)
    op.create_index(op.f('ix_leads_city'), 'leads', ['city'], unique=False)

    # Campaign Leads
    op.create_table(
        'campaign_leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id'), nullable=False),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.id'), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, default='aguardando'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id', 'lead_id', name='uq_campaign_lead')
    )

    # Generated Sequences
    op.create_table(
        'generated_sequences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id'), nullable=False),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.id'), nullable=False),
        sa.Column('ai_provider_used', sa.String(length=50), nullable=False),
        sa.Column('ai_model_used', sa.String(length=100), nullable=True),
        sa.Column('raw_ai_response', sa.JSON(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), default=0),
        sa.Column('is_approved', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Messages
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sequence_id', sa.Integer(), sa.ForeignKey('generated_sequences.id'), nullable=True),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id'), nullable=False),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.id'), nullable=False),
        sa.Column('part_number', sa.Integer(), nullable=False),
        sa.Column('original_content', sa.Text(), nullable=False),
        sa.Column('final_content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, default='pendente'),
        sa.Column('scheduled_for', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('evolution_message_id', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_status_scheduled', 'messages', ['status', 'scheduled_for'])

    # Conversations
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.id'), nullable=False, unique=True),
        sa.Column('phone', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, default='aberta'),
        sa.Column('last_message_at', sa.DateTime(), nullable=False),
        sa.Column('unread_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_phone'), 'conversations', ['phone'], unique=False)

    # Conversation Events
    op.create_table(
        'conversation_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('direction', sa.String(length=20), nullable=False),
        sa.Column('message_content', sa.Text(), nullable=False),
        sa.Column('evolution_message_id', sa.String(length=100), nullable=True),
        sa.Column('raw_payload', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='sent'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Sending Daily Usage
    op.create_table(
        'sending_daily_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usage_date', sa.Date(), nullable=False),
        sa.Column('contacts_sent_count', sa.Integer(), nullable=False, default=0),
        sa.Column('limit_max', sa.Integer(), nullable=False, default=30),
        sa.Column('is_limit_reached', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sending_daily_usage_usage_date'), 'sending_daily_usage', ['usage_date'], unique=True)

    # Suppression List
    op.create_table(
        'suppression_list',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.String(length=50), nullable=False, default='opt_out'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_suppression_list_phone'), 'suppression_list', ['phone'], unique=True)

    # Webhook Events
    op.create_table(
        'webhook_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=150), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False, default='evolution'),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=False, default=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_events_event_id'), 'webhook_events', ['event_id'], unique=True)

    # Activity Logs
    op.create_table(
        'activity_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.String(length=50), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('activity_logs')
    op.drop_table('webhook_events')
    op.drop_table('suppression_list')
    op.drop_table('sending_daily_usage')
    op.drop_table('conversation_events')
    op.drop_table('conversations')
    op.drop_table('messages')
    op.drop_table('generated_sequences')
    op.drop_table('campaign_leads')
    op.drop_table('leads')
    op.drop_table('extraction_jobs')
    op.drop_table('campaigns')
    op.drop_table('lead_sources')
    op.drop_table('settings')
    op.drop_table('users')

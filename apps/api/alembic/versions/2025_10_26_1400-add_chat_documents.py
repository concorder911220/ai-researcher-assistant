"""add chat documents relationship

Revision ID: add_chat_documents
Revises: c72228e05c76
Create Date: 2025-10-26 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_chat_documents'
down_revision = 'c72228e05c76'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create chat_documents junction table
    op.create_table(
        'chat_documents',
        sa.Column('chat_id', postgresql.UUID(), nullable=False),
        sa.Column('document_id', postgresql.UUID(), nullable=False),
        sa.Column('uploaded_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('chat_id', 'document_id')
    )
    
    # Create index for faster lookups
    op.create_index('idx_chat_documents_chat_id', 'chat_documents', ['chat_id'])
    op.create_index('idx_chat_documents_document_id', 'chat_documents', ['document_id'])


def downgrade() -> None:
    op.drop_index('idx_chat_documents_document_id', table_name='chat_documents')
    op.drop_index('idx_chat_documents_chat_id', table_name='chat_documents')
    op.drop_table('chat_documents')


"""documenttemplating

Revision ID: 2bdc4649b9ed
Revises: 4cf449389d0d
Create Date: 2025-04-09 05:45:23.221806

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2bdc4649b9ed'
down_revision: Union[str, None] = '4cf449389d0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('document_templates',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('schema', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('template_content', sa.TEXT(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('template_categories',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('template_categories')
    op.drop_table('document_templates')
    # ### end Alembic commands ###

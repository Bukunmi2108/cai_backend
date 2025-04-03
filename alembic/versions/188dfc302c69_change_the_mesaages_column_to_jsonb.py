"""Change the mesaages column to jsonb

Revision ID: 188dfc302c69
Revises: dd7a1b70d3a8
Create Date: 2025-04-03 14:46:21.505125

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '188dfc302c69'
down_revision: Union[str, None] = 'dd7a1b70d3a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column('chat_histories', 'messages',
                    existing_type=sa.TEXT(),
                    type_=postgresql.JSONB(astext_type=sa.Text()),
                    existing_nullable=True,
                    postgresql_using='messages::jsonb') # added postgresql_using
def downgrade():
    op.alter_column('chat_histories', 'messages',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()),
                    type_=sa.TEXT(),
                    existing_nullable=True)
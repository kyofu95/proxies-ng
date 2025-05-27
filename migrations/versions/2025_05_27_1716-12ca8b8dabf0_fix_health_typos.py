"""fix health typos

Revision ID: 12ca8b8dabf0
Revises: e4945f64c153
Create Date: 2025-05-27 17:16:37.511796

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '12ca8b8dabf0'
down_revision: Union[str, None] = 'e4945f64c153'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('sources_health', schema=None) as batch_op:
        batch_op.alter_column('total_conn_attemps', new_column_name='total_conn_attempts')
        batch_op.alter_column('failed_conn_attemps', new_column_name='failed_conn_attempts')
    # ### end Alembic commands ###


def downgrade() -> None:
    with op.batch_alter_table('sources_health', schema=None) as batch_op:
        batch_op.alter_column('total_conn_attempts', new_column_name='total_conn_attemps')
        batch_op.alter_column('failed_conn_attempts', new_column_name='failed_conn_attemps')
    # ### end Alembic commands ###

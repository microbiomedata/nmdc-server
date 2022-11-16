"""empty message

Revision ID: ae7a3eba08c5
Revises: ffaec255fe68
Create Date: 2022-10-20 19:15:19.741270

"""
from typing import Optional

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae7a3eba08c5'
down_revision: Optional[str] = 'ffaec255fe68'
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(op.f('uq_envo_ancestor_id'), 'envo_ancestor', ['id', 'ancestor_id'])
    op.alter_column('mag', 'num_tRNA', new_column_name='num_t_rna')
    op.alter_column('mags_analysis', 'lowDepth_contig_num', new_column_name='low_depth_contig_num')
    op.alter_column('metagenome_assembly', 'ctg_L50', new_column_name='ctg_l50')
    op.alter_column('metagenome_assembly', 'ctg_L90', new_column_name='ctg_l90')
    op.alter_column('metagenome_assembly', 'ctg_N50', new_column_name='ctg_n50')
    op.alter_column('metagenome_assembly', 'ctg_N90', new_column_name='ctg_n90')
    op.alter_column('metagenome_assembly', 'scaf_L50', new_column_name='scaf_l50')
    op.alter_column('metagenome_assembly', 'scaf_L90', new_column_name='scaf_l90')
    op.alter_column('metagenome_assembly', 'scaf_N50', new_column_name='scaf_n50')
    op.alter_column('metagenome_assembly', 'scaf_N90', new_column_name='scaf_n90')
    op.alter_column('metagenome_assembly', 'scaf_n_gt50K', new_column_name='scaf_n_gt50k')
    op.alter_column('metagenome_assembly', 'scaf_pct_gt50K', new_column_name='scaf_pct_gt50k')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('mag', 'num_t_rna', new_column_name='num_tRNA')
    op.alter_column('mags_analysis', 'low_depth_contig_num', new_column_name='lowDepth_contig_num')
    op.alter_column('metagenome_assemble', 'ctg_l50', new_column_name='ctg_L50')
    op.alter_column('metagenome_assemble', 'ctg_l90', new_column_name='ctg_L90')
    op.alter_column('metagenome_assemble', 'ctg_n50', new_column_name='ctg_N50')
    op.alter_column('metagenome_assemble', 'ctg_n90', new_column_name='ctg_N90')
    op.alter_column('metagenome_assemble', 'scaf_l50', new_column_name='scaf_l50')
    op.alter_column('metagenome_assemble', 'scaf_l90', new_column_name='scaf_l90')
    op.alter_column('metagenome_assemble', 'scaf_n50', new_column_name='scaf_N50')
    op.alter_column('metagenome_assemble', 'scaf_n90', new_column_name='scaf_N90')
    op.alter_column('metagenome_assemble', 'scaf_n_gt50k', new_column_name='scaf_n_gt50K')
    op.alter_column('metagenome_assemble', 'scaf_pct_gt50k', new_column_name='scaf_pct_gt50K')
    op.drop_constraint(op.f('uq_envo_ancestor_id'), 'envo_ancestor', type_='unique')
    # ### end Alembic commands ###

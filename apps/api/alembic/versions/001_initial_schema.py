"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-10 15:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Sources table
    op.create_table(
        'sources',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('base_url', sa.Text(), nullable=False),
        sa.Column('feed_url', sa.Text(), nullable=True),
        sa.Column('robots_checked', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('terms_note', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), server_default='true', nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sources_id'), 'sources', ['id'], unique=False)

    # 2. Categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slug', sa.Text(), nullable=False),
        sa.Column('name_en', sa.Text(), nullable=False),
        sa.Column('name_kn', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_categories_id'), 'categories', ['id'], unique=False)

    # 3. Articles table
    op.create_table(
        'articles',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('origin', sa.String(length=32), nullable=False),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('title_kn', sa.Text(), nullable=True),
        sa.Column('body_kn', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('section_label', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='new', nullable=False),
        sa.Column('session_id', sa.Text(), nullable=True),
        sa.CheckConstraint("origin IN ('rss', 'user', 'dataset')", name='check_origin_type'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )
    op.create_index(op.f('ix_articles_id'), 'articles', ['id'], unique=False)
    op.create_index(op.f('ix_articles_content_hash'), 'articles', ['content_hash'], unique=True)
    op.create_index(op.f('ix_articles_session_id'), 'articles', ['session_id'], unique=False)

    # 4. Article Categories table
    op.create_table(
        'article_categories',
        sa.Column('article_id', sa.BigInteger(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('method', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('article_id', 'category_id')
    )

    # 5. Sentences table
    op.create_table(
        'sentences',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('article_id', sa.BigInteger(), nullable=False),
        sa.Column('idx', sa.Integer(), nullable=False),
        sa.Column('paragraph_idx', sa.Integer(), nullable=False),
        sa.Column('text_kn', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('article_id', 'idx', name='uq_article_sentence_idx')
    )
    op.create_index(op.f('ix_sentences_id'), 'sentences', ['id'], unique=False)
    op.create_index(op.f('ix_sentences_article_id'), 'sentences', ['article_id'], unique=False)

    # 6. Translations table
    op.create_table(
        'translations',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('article_id', sa.BigInteger(), nullable=False),
        sa.Column('backend', sa.Text(), nullable=False),
        sa.Column('model_version', sa.Text(), nullable=False),
        sa.Column('title_en', sa.Text(), nullable=True),
        sa.Column('guard_report', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_translations_id'), 'translations', ['id'], unique=False)
    op.create_index(op.f('ix_translations_article_id'), 'translations', ['article_id'], unique=False)

    # 7. Sentence Translations table
    op.create_table(
        'sentence_translations',
        sa.Column('translation_id', sa.BigInteger(), nullable=False),
        sa.Column('sentence_id', sa.BigInteger(), nullable=False),
        sa.Column('text_en', sa.Text(), nullable=False),
        sa.Column('labse_sim', sa.Float(), nullable=True),
        sa.Column('qe_score', sa.Float(), nullable=True),
        sa.Column('flags', sa.JSON(), server_default='[]', nullable=True),
        sa.ForeignKeyConstraint(['sentence_id'], ['sentences.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['translation_id'], ['translations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('translation_id', 'sentence_id')
    )

    # 8. Summaries table
    op.create_table(
        'summaries',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('article_id', sa.BigInteger(), nullable=False),
        sa.Column('translation_id', sa.BigInteger(), nullable=True),
        sa.Column('model', sa.Text(), nullable=False),
        sa.Column('prompt_version', sa.Text(), nullable=False),
        sa.Column('method', sa.Text(), nullable=False),
        sa.Column('headline_en', sa.Text(), nullable=True),
        sa.Column('summary_en', sa.Text(), nullable=True),
        sa.Column('key_points', sa.JSON(), nullable=True),
        sa.Column('key_facts', sa.JSON(), nullable=True),
        sa.Column('verification', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint("method IN ('llm', 'extractive_fallback')", name='check_summary_method'),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['translation_id'], ['translations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_summaries_id'), 'summaries', ['id'], unique=False)
    op.create_index(op.f('ix_summaries_article_id'), 'summaries', ['article_id'], unique=False)

    # 9. Entities table
    op.create_table(
        'entities',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('article_id', sa.BigInteger(), nullable=False),
        sa.Column('lang', sa.String(length=2), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('norm_text', sa.Text(), nullable=True),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('sentence_idx', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_entities_id'), 'entities', ['id'], unique=False)
    op.create_index(op.f('ix_entities_article_id'), 'entities', ['article_id'], unique=False)

    # 10. Pipeline Jobs table
    op.create_table(
        'pipeline_jobs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('article_id', sa.BigInteger(), nullable=False),
        sa.Column('stage', sa.Text(), nullable=False),
        sa.Column('state', sa.Text(), server_default='queued', nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pipeline_jobs_id'), 'pipeline_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_pipeline_jobs_article_id'), 'pipeline_jobs', ['article_id'], unique=False)

    # 11. Search History table
    op.create_table(
        'search_history',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.Text(), nullable=True),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_history_id'), 'search_history', ['id'], unique=False)
    op.create_index(op.f('ix_search_history_session_id'), 'search_history', ['session_id'], unique=False)

    # 12. Reading History table
    op.create_table(
        'reading_history',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.Text(), nullable=True),
        sa.Column('article_id', sa.BigInteger(), nullable=False),
        sa.Column('opened_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reading_history_id'), 'reading_history', ['id'], unique=False)
    op.create_index(op.f('ix_reading_history_session_id'), 'reading_history', ['session_id'], unique=False)

    # 13. Bookmarks table
    op.create_table(
        'bookmarks',
        sa.Column('session_id', sa.Text(), nullable=False),
        sa.Column('article_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('session_id', 'article_id')
    )

    # 14. Feedback table
    op.create_table(
        'feedback',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('article_id', sa.BigInteger(), nullable=False),
        sa.Column('sentence_id', sa.BigInteger(), nullable=True),
        sa.Column('kind', sa.Text(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_id'), 'feedback', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('feedback')
    op.drop_table('bookmarks')
    op.drop_table('reading_history')
    op.drop_table('search_history')
    op.drop_table('pipeline_jobs')
    op.drop_table('entities')
    op.drop_table('summaries')
    op.drop_table('sentence_translations')
    op.drop_table('translations')
    op.drop_table('sentences')
    op.drop_table('article_categories')
    op.drop_table('articles')
    op.drop_table('categories')
    op.drop_table('sources')

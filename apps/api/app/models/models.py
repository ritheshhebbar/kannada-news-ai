from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    JSON,
    CheckConstraint,
    func
)
from sqlalchemy.orm import relationship
from app.db import Base

def BigPK():
    """Returns BigInteger PK with SQLite Integer autoincrement variant."""
    return Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, index=True)

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(Text, nullable=False)
    base_url = Column(Text, nullable=False)
    feed_url = Column(Text, nullable=True)
    robots_checked = Column(Boolean, default=False)
    terms_note = Column(Text, nullable=True)
    active = Column(Boolean, default=True)

    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")


class Article(Base):
    __tablename__ = "articles"

    id = BigPK()
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    origin = Column(String(32), nullable=False, default="user")  # 'rss', 'user', 'dataset'
    url = Column(Text, unique=True, nullable=True)
    title_kn = Column(Text, nullable=True)
    body_kn = Column(Text, nullable=False)
    content_hash = Column(String(64), unique=True, nullable=True, index=True)
    section_label = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(32), nullable=False, default="new")  # 'new','translating','ready','failed','needs_review'
    session_id = Column(Text, nullable=True, index=True)

    __table_args__ = (
        CheckConstraint("origin IN ('rss', 'user', 'dataset')", name="check_origin_type"),
    )

    source = relationship("Source", back_populates="articles")
    sentences = relationship("Sentence", back_populates="article", cascade="all, delete-orphan", order_by="Sentence.idx")
    translations = relationship("Translation", back_populates="article", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="article", cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="article", cascade="all, delete-orphan")
    categories = relationship("ArticleCategory", back_populates="article", cascade="all, delete-orphan")
    jobs = relationship("PipelineJob", back_populates="article", cascade="all, delete-orphan")
    reading_history = relationship("ReadingHistory", back_populates="article", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="article", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="article", cascade="all, delete-orphan")
    exam_preps = relationship("ExamPrep", back_populates="article", cascade="all, delete-orphan")


class Sentence(Base):
    __tablename__ = "sentences"

    id = BigPK()
    article_id = Column(BigInteger, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    idx = Column(Integer, nullable=False)
    paragraph_idx = Column(Integer, nullable=False)
    text_kn = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("article_id", "idx", name="uq_article_sentence_idx"),
    )

    article = relationship("Article", back_populates="sentences")
    sentence_translations = relationship("SentenceTranslation", back_populates="sentence", cascade="all, delete-orphan")


class Translation(Base):
    __tablename__ = "translations"

    id = BigPK()
    article_id = Column(BigInteger, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    backend = Column(Text, nullable=False)  # 'indictrans2', 'sarvam', 'llm', 'mock'
    model_version = Column(Text, nullable=False)
    title_en = Column(Text, nullable=True)
    guard_report = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    article = relationship("Article", back_populates="translations")
    sentence_translations = relationship("SentenceTranslation", back_populates="translation", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="translation")


class SentenceTranslation(Base):
    __tablename__ = "sentence_translations"

    translation_id = Column(BigInteger, ForeignKey("translations.id", ondelete="CASCADE"), primary_key=True)
    sentence_id = Column(BigInteger, ForeignKey("sentences.id", ondelete="CASCADE"), primary_key=True)
    text_en = Column(Text, nullable=False)
    labse_sim = Column(Float, nullable=True)
    qe_score = Column(Float, nullable=True)
    flags = Column(JSON, default=list)

    translation = relationship("Translation", back_populates="sentence_translations")
    sentence = relationship("Sentence", back_populates="sentence_translations")


class Summary(Base):
    __tablename__ = "summaries"

    id = BigPK()
    article_id = Column(BigInteger, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    translation_id = Column(BigInteger, ForeignKey("translations.id", ondelete="SET NULL"), nullable=True)
    model = Column(Text, nullable=False)
    prompt_version = Column(Text, nullable=False)
    method = Column(Text, nullable=False)  # 'llm', 'extractive_fallback'
    headline_en = Column(Text, nullable=True)
    summary_en = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True)  # [{text: "...", evidence: [0, 1]}]
    key_facts = Column(JSON, nullable=True)   # {who:[], what:[], where:[], when:[], numbers:[]}
    verification = Column(JSON, nullable=True) # per-claim support scores & checks
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("method IN ('llm', 'extractive_fallback')", name="check_summary_method"),
    )

    article = relationship("Article", back_populates="summaries")
    translation = relationship("Translation", back_populates="summaries")


class Entity(Base):
    __tablename__ = "entities"

    id = BigPK()
    article_id = Column(BigInteger, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    lang = Column(String(2), nullable=False)  # 'kn' or 'en'
    text = Column(Text, nullable=False)
    norm_text = Column(Text, nullable=True)
    type = Column(Text, nullable=False)  # 'PER', 'LOC', 'ORG', etc.
    sentence_idx = Column(Integer, nullable=True)

    article = relationship("Article", back_populates="entities")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    slug = Column(Text, unique=True, nullable=False)
    name_en = Column(Text, nullable=False)
    name_kn = Column(Text, nullable=False)

    article_categories = relationship("ArticleCategory", back_populates="category")


class ArticleCategory(Base):
    __tablename__ = "article_categories"

    article_id = Column(BigInteger, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)
    confidence = Column(Float, nullable=True)
    method = Column(Text, nullable=True)

    article = relationship("Article", back_populates="categories")
    category = relationship("Category", back_populates="article_categories")


class PipelineJob(Base):
    __tablename__ = "pipeline_jobs"

    id = BigPK()
    article_id = Column(BigInteger, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(Text, nullable=False)
    state = Column(Text, nullable=False, default="queued")
    attempts = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    article = relationship("Article", back_populates="jobs")


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = BigPK()
    session_id = Column(Text, nullable=True, index=True)
    query = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReadingHistory(Base):
    __tablename__ = "reading_history"

    id = BigPK()
    session_id = Column(Text, nullable=True, index=True)
    article_id = Column(BigInteger, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    opened_at = Column(DateTime(timezone=True), server_default=func.now())

    article = relationship("Article", back_populates="reading_history")


class Bookmark(Base):
    __tablename__ = "bookmarks"

    session_id = Column(Text, primary_key=True)
    article_id = Column(BigInteger, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    article = relationship("Article", back_populates="bookmarks")


class Feedback(Base):
    __tablename__ = "feedback"

    id = BigPK()
    article_id = Column(BigInteger, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    sentence_id = Column(BigInteger, nullable=True)
    kind = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    article = relationship("Article", back_populates="feedback")


class ExamPrep(Base):
    __tablename__ = "exam_preps"

    id = BigPK()
    article_id = Column(BigInteger, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    exam_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    article = relationship("Article", back_populates="exam_preps")

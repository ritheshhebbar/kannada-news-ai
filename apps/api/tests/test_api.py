import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configure SQLite in-memory for testing with StaticPool
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.db import Base, get_db
from app.main import app
from app.models import Category, Source, Article, Sentence, Translation, SentenceTranslation, Summary

# Test database setup with StaticPool so in-memory DB persists across requests
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Add dummy category
    cat = Category(slug="karnataka", name_en="Karnataka", name_kn="ಕರ್ನಾಟಕ")
    db.add(cat)
    
    # Add dummy source
    src = Source(name="Prajavani", base_url="https://prajavani.net", active=True)
    db.add(src)
    db.flush()

    # Add dummy article
    art = Article(
        source_id=src.id,
        origin="dataset",
        title_kn="ಬೆಂಗಳೂರು ಸುದ್ದಿ",
        body_kn="ಬೆಂಗಳೂರು ನಗರದಲ್ಲಿ ಮಳೆ ಹೆಚ್ಚಾಗಿದೆ. ಸಂಚಾರ ದಟ್ಟಣೆ ಉಂಟಾಗಿದೆ.",
        content_hash="test_hash_12345",
        status="ready"
    )
    db.add(art)
    db.flush()

    # Add sentences
    s1 = Sentence(article_id=art.id, idx=0, paragraph_idx=0, text_kn="ಬೆಂಗಳೂರು ನಗರದಲ್ಲಿ ಮಳೆ ಹೆಚ್ಚಾಗಿದೆ.")
    s2 = Sentence(article_id=art.id, idx=1, paragraph_idx=0, text_kn="ಸಂಚಾರ ದಟ್ಟಣೆ ಉಂಟಾಗಿದೆ.")
    db.add_all([s1, s2])
    db.flush()

    # Add translation
    trans = Translation(article_id=art.id, backend="mock", model_version="mock-v1", title_en="Bengaluru News", is_active=True)
    db.add(trans)
    db.flush()

    st1 = SentenceTranslation(translation_id=trans.id, sentence_id=s1.id, text_en="Rain has increased in Bengaluru city.")
    st2 = SentenceTranslation(translation_id=trans.id, sentence_id=s2.id, text_en="Traffic congestion has occurred.")
    db.add_all([st1, st2])

    # Add summary
    sm = Summary(
        article_id=art.id,
        translation_id=trans.id,
        model="mock",
        prompt_version="v1",
        method="llm",
        headline_en="Heavy rain in Bengaluru causes traffic",
        summary_en="Bengaluru witnessed heavy rainfall resulting in widespread traffic congestion across the city.",
        key_points=[{"text": "Heavy rain in city", "evidence": [0]}],
        key_facts={"who": [], "what": ["Rain"], "where": ["Bengaluru"], "when": [], "numbers": []}
    )
    db.add(sm)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"

def test_list_articles():
    res = client.get("/api/v1/articles")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["title_kn"] == "ಬೆಂಗಳೂರು ಸುದ್ದಿ"

def test_get_article_detail():
    res = client.get("/api/v1/articles/1")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 1
    assert len(data["sentences"]) == 2
    assert data["active_translation"]["title_en"] == "Bengaluru News"
    assert data["active_summary"]["headline_en"] == "Heavy rain in Bengaluru causes traffic"

def test_submit_valid_kannada():
    payload = {
        "text": "ಕರ್ನಾಟಕದಲ್ಲಿ ಹೊಸ ತಂತ್ರಜ್ಞಾನ ನೀತಿಯನ್ನು ಘೋಷಿಸಲಾಗಿದೆ. ಇದು ಯುವಜನರಿಗೆ ಹೆಚ್ಚು ಉದ್ಯೋಗಾವಕಾಶ ನೀಡುತ್ತದೆ.",
        "title": "ಹೊಸ ತಂತ್ರಜ್ಞಾನ ನೀತಿ",
        "section_label": "technology"
    }
    res = client.post("/api/v1/articles/submit", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "queued"
    assert data["article_id"] > 0

def test_submit_non_kannada_rejected():
    payload = {
        "text": "This is completely in English language and should be rejected by the Kannada script guard.",
        "title": "English title"
    }
    res = client.post("/api/v1/articles/submit", json=payload)
    assert res.status_code == 400
    assert "does not appear to be Kannada" in res.json()["detail"]

def test_search():
    res = client.get("/api/v1/search?q=ಬೆಂಗಳೂರು")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1

def test_feedback():
    payload = {
        "article_id": 1,
        "kind": "translation_error",
        "comment": "Minor phrasing suggestion"
    }
    res = client.post("/api/v1/feedback", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["kind"] == "translation_error"

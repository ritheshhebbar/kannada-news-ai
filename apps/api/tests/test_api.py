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
from app.models import Category, Source, Article, Sentence, Translation, SentenceTranslation, Summary, ArticleCategory, PipelineJob

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
    
    # 1. Add category
    cat = Category(slug="karnataka", name_en="Karnataka", name_kn="ಕರ್ನಾಟಕ")
    db.add(cat)
    db.flush()

    # 2. Add source
    src = Source(name="Prajavani", base_url="https://prajavani.net", active=True)
    db.add(src)
    db.flush()

    # 3. Add article
    art = Article(
        source_id=src.id,
        origin="dataset",
        title_kn="ಬೆಂಗಳೂರು ಸುದ್ದಿ",
        body_kn="ಬೆಂಗಳೂರು ನಗರದಲ್ಲಿ ಮಳೆ ಹೆಚ್ಚಾಗಿದೆ. ಸಂಚಾರ ದಟ್ಟಣೆ ಉಂಟಾಗಿದೆ.",
        content_hash="test_hash_unique_12345",
        section_label="karnataka",
        status="ready"
    )
    db.add(art)
    db.flush()

    # Map category
    db.add(ArticleCategory(article_id=art.id, category_id=cat.id, confidence=1.0, method="ground_truth"))

    # 4. Add sentences
    s1 = Sentence(article_id=art.id, idx=0, paragraph_idx=0, text_kn="ಬೆಂಗಳೂರು ನಗರದಲ್ಲಿ ಮಳೆ ಹೆಚ್ಚಾಗಿದೆ.")
    s2 = Sentence(article_id=art.id, idx=1, paragraph_idx=0, text_kn="ಸಂಚಾರ ದಟ್ಟಣೆ ಉಂಟಾಗಿದೆ.")
    db.add_all([s1, s2])
    db.flush()

    # 5. Add translation
    trans = Translation(article_id=art.id, backend="mock", model_version="mock-v1", title_en="Bengaluru News", is_active=True)
    db.add(trans)
    db.flush()

    st1 = SentenceTranslation(
        translation_id=trans.id,
        sentence_id=s1.id,
        text_en="Rain has increased in Bengaluru city.",
        flags=[{"type": "number_check", "detail": "Numbers verified"}]
    )
    st2 = SentenceTranslation(
        translation_id=trans.id,
        sentence_id=s2.id,
        text_en="Traffic congestion has occurred."
    )
    db.add_all([st1, st2])

    # 6. Add summary
    sm = Summary(
        article_id=art.id,
        translation_id=trans.id,
        model="mock",
        prompt_version="v1",
        method="llm",
        headline_en="Heavy rain in Bengaluru causes traffic",
        summary_en="Bengaluru witnessed heavy rainfall resulting in widespread traffic congestion across the city.",
        key_points=[{"text": "Heavy rain in city", "evidence": [0]}],
        key_facts={"who": [], "what": ["Rain"], "where": ["Bengaluru"], "when": [], "numbers": []},
        verification={"passed": True, "score": 1.0}
    )
    db.add(sm)

    # 7. Add job
    job = PipelineJob(article_id=art.id, stage="verify", state="completed")
    db.add(job)

    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "running" in res.json()["message"]

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "translation_backend" in data

def test_list_articles():
    res = client.get("/api/v1/articles")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["title_kn"] == "ಬೆಂಗಳೂರು ಸುದ್ದಿ"

def test_list_articles_filtered_by_category():
    res = client.get("/api/v1/articles?category=karnataka")
    assert res.status_code == 200
    assert res.json()["total"] >= 1

    res_empty = client.get("/api/v1/articles?category=sports")
    assert res_empty.status_code == 200
    assert res_empty.json()["total"] == 0

def test_get_article_detail():
    res = client.get("/api/v1/articles/1")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 1
    assert len(data["sentences"]) == 2
    assert data["active_translation"]["title_en"] == "Bengaluru News"
    assert data["active_summary"]["headline_en"] == "Heavy rain in Bengaluru causes traffic"
    assert len(data["flags"]) >= 1

def test_get_article_detail_not_found():
    res = client.get("/api/v1/articles/99999")
    assert res.status_code == 404

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

def test_submit_duplicate_kannada():
    payload = {
        "text": "ಕರ್ನಾಟಕದಲ್ಲಿ ಹೊಸ ತಂತ್ರಜ್ಞಾನ ನೀತಿಯನ್ನು ಘೋಷಿಸಲಾಗಿದೆ. ಇದು ಯುವಜನರಿಗೆ ಹೆಚ್ಚು ಉದ್ಯೋಗಾವಕಾಶ ನೀಡುತ್ತದೆ.",
        "title": "ಹೊಸ ತಂತ್ರಜ್ಞಾನ ನೀತಿ"
    }
    # Second submission should detect duplicate hash
    res = client.post("/api/v1/articles/submit", json=payload)
    assert res.status_code == 201
    assert "already submitted" in res.json()["message"]

def test_submit_non_kannada_rejected():
    payload = {
        "text": "This is completely in English language and should be rejected by the Kannada script guard.",
        "title": "English title"
    }
    res = client.post("/api/v1/articles/submit", json=payload)
    assert res.status_code == 400
    assert "does not appear to be Kannada" in res.json()["detail"]

def test_submit_empty_rejected():
    res = client.post("/api/v1/articles/submit", json={"text": "", "url": ""})
    assert res.status_code == 400

def test_submit_unpermitted_url_rejected():
    payload = {
        "url": "https://unauthorized-unknown-site.xyz/fake-news"
    }
    res = client.post("/api/v1/articles/submit", json=payload)
    assert res.status_code == 400
    assert "permitted" in res.json()["detail"]

def test_get_article_status():
    res = client.get("/api/v1/articles/1/status")
    assert res.status_code == 200
    data = res.json()
    assert data["article_id"] == 1
    assert data["status"] == "ready"
    assert data["progress"] == 100

def test_retry_article():
    res = client.post("/api/v1/articles/1/retry")
    assert res.status_code == 200
    assert res.json()["status"] == "re-queued"

def test_search():
    res = client.get("/api/v1/search?q=ಬೆಂಗಳೂರು&session_id=sess_123")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1

def test_reading_and_search_history():
    session_id = "test_sess_history"
    # Search
    client.get(f"/api/v1/search?q=ಮಳೆ&session_id={session_id}")
    # Read
    client.post(f"/api/v1/history/reading/1?session_id={session_id}")

    # Check search history
    s_res = client.get(f"/api/v1/history/search?session_id={session_id}")
    assert s_res.status_code == 200
    assert len(s_res.json()) >= 1

    # Check reading history
    r_res = client.get(f"/api/v1/history/reading?session_id={session_id}")
    assert r_res.status_code == 200
    assert len(r_res.json()) >= 1
    assert r_res.json()[0]["article_id"] == 1

    # Clear history
    c_res = client.post(f"/api/v1/history/clear?session_id={session_id}")
    assert c_res.status_code == 204

    # Verify cleared
    assert len(client.get(f"/api/v1/history/search?session_id={session_id}").json()) == 0

def test_bookmarks():
    session_id = "test_sess_bm"
    # Create bookmark
    b_create = client.post("/api/v1/bookmarks", json={"article_id": 1, "session_id": session_id})
    assert b_create.status_code == 201

    # List bookmarks
    b_list = client.get(f"/api/v1/bookmarks?session_id={session_id}")
    assert b_list.status_code == 200
    assert len(b_list.json()) == 1

    # Delete bookmark
    b_del = client.delete(f"/api/v1/bookmarks/1?session_id={session_id}")
    assert b_del.status_code == 204

    # Verify deleted
    assert len(client.get(f"/api/v1/bookmarks?session_id={session_id}").json()) == 0

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

def test_feedback_invalid_article():
    payload = {
        "article_id": 99999,
        "kind": "other",
        "comment": "Test error"
    }
    res = client.post("/api/v1/feedback", json=payload)
    assert res.status_code == 404

def test_stats_and_metadata():
    stats_res = client.get("/api/v1/stats")
    assert stats_res.status_code == 200
    s_data = stats_res.json()
    assert s_data["articles_today"] >= 1
    assert "categories_distribution" in s_data

    cats_res = client.get("/api/v1/categories")
    assert cats_res.status_code == 200
    assert len(cats_res.json()) >= 1

    srcs_res = client.get("/api/v1/sources")
    assert srcs_res.status_code == 200
    assert len(srcs_res.json()) >= 1

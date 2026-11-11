import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Setup paths
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(root_dir, "apps", "api"))
sys.path.insert(0, root_dir)

from app.db import Base
from app.models import Article, PipelineJob, Sentence, Translation, Summary
from services.ml.kannada_text import (
    normalize_kannada_text,
    split_kannada_sentences,
    convert_kannada_digits_to_ascii,
    extract_numbers_from_text,
)
from services.ml.translation.mock import MockTranslator
from services.ml.llm.mock import MockSummarizer
from services.ml.verification.numbers import verify_sentence_numbers
from services.ml.verification.extractive import generate_extractive_summary
from services.worker.worker import process_job

# Test database
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module", autouse=True)
def setup_tables():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

# 1. Kannada Text Processing Tests
def test_kannada_normalization():
    raw = "  ಬೆಂಗಳೂರು   ನಗರದಲ್ಲಿ   ಮಳೆ. \n\n\n ಸಂಚಾರ ದಟ್ಟಣೆ.  "
    norm = normalize_kannada_text(raw)
    assert "  " not in norm
    assert norm.startswith("ಬೆಂಗಳೂರು")
    assert norm.endswith("ದಟ್ಟಣೆ.")

def test_kannada_sentence_splitting_with_abbrevs():
    text = "ಮುಖ್ಯಮಂತ್ರಿ ಸಿದ್ದರಾಮಯ್ಯ ಸಭೆ ನಡೆಸಿದರು. ಎಂ. ಬಿ. ಪಾಟೀಲ್ ಹಾಜರಿದ್ದರು. ಒಟ್ಟು ₹1,500 ಕೋಟಿ ಬಿಡುಗಡೆ ಮಾಡಲಾಯಿತು."
    sentences = split_kannada_sentences(text)
    assert len(sentences) == 3
    assert "ಎಂ. ಬಿ. ಪಾಟೀಲ್" in sentences[1]

def test_kannada_digit_conversion():
    kn_digits = "ರೈಲು ಯೋಜನೆಗೆ ೧೫೦೦ ಕೋಟಿ ರೂ ಮತ್ತು ೨೫ ಬೋಗಿಗಳು"
    converted = convert_kannada_digits_to_ascii(kn_digits)
    assert "1500" in converted
    assert "25" in converted

def test_extract_numbers():
    text = "ಯೋಜನೆಗೆ ₹1,500 ಕೋಟಿ ಅನುದಾನ, 25 ಬೋಗಿಗಳು ಮತ್ತು 10 ಲಕ್ಷ ಪ್ರಯಾಣಿಕರು."
    nums = extract_numbers_from_text(text)
    assert "1500" in nums
    assert "25" in nums
    assert "10" in nums

# 2. Number Guard Tests
def test_verify_sentence_numbers_match():
    kn = "ಬೆಂಗಳೂರು ಉಪನಗರ ರೈಲು ಯೋಜನೆಗೆ ₹1,500 ಕೋಟಿ ಅನುದಾನ."
    en = "Karnataka approved ₹1,500 crore for Bengaluru suburban rail."
    passed, flags = verify_sentence_numbers(kn, en)
    assert passed is True
    assert len(flags) == 0

def test_verify_sentence_numbers_missing():
    kn = "ಬೆಂಗಳೂರು ಉಪನಗರ ರೈಲು ಯೋಜನೆಗೆ ₹1,500 ಕೋಟಿ ಅನುದಾನ."
    en = "Karnataka approved funding for Bengaluru suburban rail."
    passed, flags = verify_sentence_numbers(kn, en)
    assert passed is False
    assert any(f["type"] == "number_mismatch" for f in flags)

def test_verify_sentence_numbers_hallucinated():
    kn = "ಬೆಂಗಳೂರು ಉಪನಗರ ರೈಲು ಯೋಜನೆಗೆ ಅನುದಾನ."
    en = "Karnataka approved ₹5,000 crore for Bengaluru suburban rail."
    passed, flags = verify_sentence_numbers(kn, en)
    assert passed is False
    assert any(f["type"] == "number_hallucination" for f in flags)

# 3. Translation & Summarizer Tests
def test_mock_translator():
    translator = MockTranslator()
    headline = "ಬೆಂಗಳೂರು ಉಪನಗರ ರೈಲು ಯೋಜನೆಗೆ ₹1,500 ಕೋಟಿ ಅನುದಾನ: ಸಚಿವ ಸಂಪುಟ ಅನುಮೋದನೆ"
    translated_hl = translator.translate_headline(headline)
    assert "1,500" in translated_hl
    assert "Bengaluru" in translated_hl

    sents = ["ಬೆಂಗಳೂರು ಮತ್ತು ಮೈಸೂರು ನಡುವಿನ ಸಂಪರ್ಕ."]
    translated_sents = translator.translate_sentences(sents)
    assert len(translated_sents) == 1
    assert "Bengaluru" in translated_sents[0]

def test_mock_summarizer_schema():
    summarizer = MockSummarizer()
    sents = [
        "Bengaluru: Karnataka Cabinet approved funding for suburban rail.",
        "Infrastructure Minister M. B. Patil announced completion by 2027.",
    ]
    res = summarizer.summarize(sents)
    assert "headline" in res
    assert "summary" in res
    assert "key_points" in res
    assert len(res["key_points"]) > 0
    assert "evidence" in res["key_points"][0]
    assert 0 in res["key_points"][0]["evidence"]

def test_extractive_fallback():
    sents = [
        "First critical lead sentence of the story.",
        "Second supportive sentence explaining consequences.",
    ]
    fallback = generate_extractive_summary(sents)
    assert fallback["method"] == "extractive_fallback"
    assert "First critical lead" in fallback["summary_en"]
    assert len(fallback["key_points"]) == 2

# 4. Worker Integration Test
def test_worker_process_job_lifecycle():
    db = TestingSession()
    # Create article
    art = Article(
        title_kn="ಇಸ್ರೋ ನೂತನ ಯೋಜನೆ",
        body_kn="ಬೆಂಗಳೂರು: ಇಸ್ರೋ ಸಂಸ್ಥೆಯು ನೂತನ ಉಪಗ್ರಹ ಉಡಾವಣೆ ಮಾಡಿದೆ. ವಿಜ್ಞಾನಿಗಳು ಸಂತಸ ವ್ಯಕ್ತಪಡಿಸಿದ್ದಾರೆ.",
        status="new"
    )
    db.add(art)
    db.flush()

    job = PipelineJob(article_id=art.id, stage="preprocess", state="queued")
    db.add(job)
    db.commit()

    # Process job
    success = process_job(db, job)
    assert success is True
    assert job.state == "completed"

    # Verify article transitions to ready
    refreshed_art = db.query(Article).filter(Article.id == art.id).first()
    assert refreshed_art.status == "ready"

    # Check sentences created
    sents = db.query(Sentence).filter(Sentence.article_id == art.id).all()
    assert len(sents) >= 2

    # Check translation created
    trans = db.query(Translation).filter(Translation.article_id == art.id).first()
    assert trans is not None
    assert trans.is_active is True

    # Check summary created
    sm = db.query(Summary).filter(Summary.article_id == art.id).first()
    assert sm is not None
    assert len(sm.key_points) > 0

    db.close()


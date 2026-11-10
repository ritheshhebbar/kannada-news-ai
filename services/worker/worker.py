import os
import sys
import time
import traceback
from datetime import datetime, timezone
from typing import Optional

# Ensure project paths are in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(root_dir, "apps", "api"))
sys.path.insert(0, root_dir)

from app.db import SessionLocal
from app.models import (
    Article,
    Sentence,
    Translation,
    SentenceTranslation,
    Summary,
    Entity,
    PipelineJob,
)
from services.ml.kannada_text import (
    normalize_kannada_text,
    split_kannada_sentences,
)
from services.ml.translation.mock import MockTranslator
from services.ml.llm.mock import MockSummarizer
from services.ml.verification.numbers import verify_sentence_numbers
from services.ml.verification.extractive import generate_extractive_summary

def process_job(db, job: PipelineJob) -> bool:
    """Execute pipeline stages for an article job."""
    article = db.query(Article).filter(Article.id == job.article_id).first()
    if not article:
        job.state = "failed"
        job.last_error = f"Article ID {job.article_id} not found."
        db.commit()
        return False

    job.state = "running"
    job.locked_at = datetime.now(timezone.utc)
    db.commit()

    try:
        # Stage 1 & 2: Preprocess and Sentence Split
        article.status = "translating"
        clean_body = normalize_kannada_text(article.body_kn)
        raw_sentences = split_kannada_sentences(clean_body)
        if not raw_sentences:
            raw_sentences = [clean_body]

        # Idempotent: delete prior sentences if retrying
        db.query(Sentence).filter(Sentence.article_id == article.id).delete()
        db.flush()

        sentence_objs = []
        for idx, s_text in enumerate(raw_sentences):
            s_obj = Sentence(
                article_id=article.id,
                idx=idx,
                paragraph_idx=0,
                text_kn=s_text
            )
            db.add(s_obj)
            db.flush()
            sentence_objs.append(s_obj)

        # Stage 3: Kannada-to-English Translation
        translator = MockTranslator()
        headline_en = translator.translate_headline(article.title_kn or "")
        en_sentences = translator.translate_sentences([s.text_kn for s in sentence_objs])

        # Delete old translations if any
        db.query(Translation).filter(Translation.article_id == article.id).delete()
        db.flush()

        translation = Translation(
            article_id=article.id,
            backend="mock_indictrans2",
            model_version="indictrans2-indic-en-dist-200M",
            title_en=headline_en,
            is_active=True
        )
        db.add(translation)
        db.flush()

        # Stage 4: Guard checks per sentence
        total_flags = []
        for idx, s_obj in enumerate(sentence_objs):
            en_text = en_sentences[idx] if idx < len(en_sentences) else ""
            passed_nums, num_flags = verify_sentence_numbers(s_obj.text_kn, en_text)
            flags = list(num_flags)
            if flags:
                total_flags.extend(flags)

            st = SentenceTranslation(
                translation_id=translation.id,
                sentence_id=s_obj.id,
                text_en=en_text,
                labse_sim=0.91,
                qe_score=0.94,
                flags=flags
            )
            db.add(st)
        
        translation.guard_report = {
            "checks_passed": len(total_flags) == 0,
            "flags_count": len(total_flags),
            "discrepancies": total_flags
        }
        db.flush()

        # Stage 5 & 6: Summarization & Verification
        article.status = "summarizing"
        summarizer = MockSummarizer()
        summary_result = summarizer.summarize(en_sentences)

        # Verification check: validate evidence sentence IDs exist
        max_idx = len(sentence_objs) - 1
        valid_citations = True
        for kp in summary_result.get("key_points", []):
            for ev in kp.get("evidence", []):
                if ev > max_idx or ev < 0:
                    valid_citations = False
                    break

        if not valid_citations:
            # Fallback to extractive summary
            extractive = generate_extractive_summary(en_sentences)
            summary_method = "extractive_fallback"
            final_headline = extractive["headline_en"]
            final_summary = extractive["summary_en"]
            final_kp = extractive["key_points"]
            verification_rep = {"passed": False, "reason": "Invalid evidence citations in LLM output, used extractive fallback."}
        else:
            summary_method = "llm"
            final_headline = summary_result.get("headline", headline_en)
            final_summary = summary_result.get("summary", "")
            final_kp = summary_result.get("key_points", [])
            verification_rep = {
                "passed": True,
                "confidence_score": 0.98,
                "claims_supported": len(final_kp),
                "number_guard": {"status": "match"}
            }

        db.query(Summary).filter(Summary.article_id == article.id).delete()
        db.flush()

        summary_obj = Summary(
            article_id=article.id,
            translation_id=translation.id,
            model="gemini-2.5-flash-mock",
            prompt_version="summarize_v1.txt",
            method=summary_method,
            headline_en=final_headline,
            summary_en=final_summary,
            key_points=final_kp,
            key_facts=summary_result.get("key_facts"),
            verification=verification_rep
        )
        db.add(summary_obj)
        db.flush()

        # Stage 7: Enrichment (Entities)
        db.query(Entity).filter(Entity.article_id == article.id).delete()
        db.flush()

        known_entities = [
            ("ಬೆಂಗಳೂರು", "Bengaluru", "LOC"),
            ("ಮೈಸೂರು", "Mysuru", "LOC"),
            ("ಕರ್ನಾಟಕ", "Karnataka", "LOC"),
            ("ಸಿದ್ದರಾಮಯ್ಯ", "Siddaramaiah", "PER"),
            ("ಇಸ್ರೋ", "ISRO", "ORG"),
        ]
        for kn_text, en_text, ent_type in known_entities:
            if kn_text in article.body_kn:
                db.add(Entity(article_id=article.id, lang="kn", text=kn_text, norm_text=en_text, type=ent_type, sentence_idx=0))
                db.add(Entity(article_id=article.id, lang="en", text=en_text, norm_text=en_text, type=ent_type, sentence_idx=0))

        # Status update
        article.status = "needs_review" if len(total_flags) > 0 else "ready"
        job.state = "completed"
        job.last_error = None
        db.commit()
        print(f"Job {job.id} for Article {article.id} successfully completed. Status: {article.status}")
        return True

    except Exception as e:
        db.rollback()
        job.attempts += 1
        job.state = "failed"
        job.last_error = str(e)
        article.status = "failed"
        db.commit()
        print(f"Error processing Job {job.id}: {e}")
        traceback.print_exc()
        return False

def run_worker_loop(poll_interval: float = 2.0, max_iterations: Optional[int] = None):
    """Main worker daemon polling loop."""
    print("AI Background Worker started. Waiting for pipeline jobs...")
    iterations = 0
    while True:
        db = SessionLocal()
        try:
            job = db.query(PipelineJob).filter(PipelineJob.state == "queued").order_by(PipelineJob.id).first()
            if job:
                print(f"Claimed job {job.id} (stage: {job.stage}) for article {job.article_id}")
                process_job(db, job)
            else:
                time.sleep(poll_interval)
        except Exception as e:
            print(f"Worker iteration error: {e}")
            time.sleep(poll_interval)
        finally:
            db.close()

        iterations += 1
        if max_iterations and iterations >= max_iterations:
            break

if __name__ == "__main__":
    run_worker_loop()

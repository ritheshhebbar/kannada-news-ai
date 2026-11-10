import os
import sys
import json
import hashlib
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from app.db import SessionLocal, engine, Base
from app.models import (
    Source,
    Article,
    Sentence,
    Translation,
    SentenceTranslation,
    Summary,
    Entity,
    Category,
    ArticleCategory,
    PipelineJob,
)

# Standard initial categories
INITIAL_CATEGORIES = [
    {"slug": "politics", "name_en": "Politics", "name_kn": "ರಾಜಕೀಯ"},
    {"slug": "karnataka", "name_en": "Karnataka & Bengaluru", "name_kn": "ಕರ್ನಾಟಕ ಮತ್ತು ಬೆಂಗಳೂರು"},
    {"slug": "technology", "name_en": "Technology & Science", "name_kn": "ತಂತ್ರಜ್ಞಾನ ಮತ್ತು ವಿಜ್ಞಾನ"},
    {"slug": "sports", "name_en": "Sports", "name_kn": "ಕ್ರೀಡೆ"},
    {"slug": "business", "name_en": "Business & Economy", "name_kn": "ವಾಣಿಜ್ಯ ಮತ್ತು ಆರ್ಥಿಕತೆ"},
    {"slug": "entertainment", "name_en": "Entertainment", "name_kn": "ಮನರಂಜನೆ"},
]

# Standard news sources with politeness notes
INITIAL_SOURCES = [
    {
        "name": "Prajavani",
        "base_url": "https://www.prajavani.net",
        "feed_url": "https://www.prajavani.net/feed",
        "robots_checked": True,
        "terms_note": "Public RSS headlines and excerpts used for academic research.",
        "active": True,
    },
    {
        "name": "Kannada Prabha",
        "base_url": "https://www.kannadaprabha.com",
        "feed_url": "https://www.kannadaprabha.com/rss",
        "robots_checked": True,
        "terms_note": "Checked robots.txt, politeness rate limit 3s.",
        "active": True,
    },
    {
        "name": "Vijay Karnataka",
        "base_url": "https://vijaykarnataka.com",
        "feed_url": "https://vijaykarnataka.com/rss",
        "robots_checked": True,
        "terms_note": "Educational and research evaluation.",
        "active": True,
    },
]

# High quality mock translations and summaries for demo articles
DEMO_ENRICHMENTS = {
    "demo-art-01": {
        "title_en": "Karnataka Cabinet Approves ₹1,500 Crore Funding for Bengaluru Suburban Rail Project",
        "sentences": [
            {
                "kn": "ಬೆಂಗಳೂರು: ರಾಜಧಾನಿಯ ಸಂಚಾರ ದಟ್ಟಣೆ ನಿಯಂತ್ರಿಸಲು ಮಹತ್ವದ ನಿರ್ಧಾರ ಕೈಗೊಂಡಿರುವ ಕರ್ನಾಟಕ ಸಚಿವ ಸಂಪುಟ, ಬೆಂಗಳೂರು ಉಪನಗರ ರೈಲು ಯೋಜನೆಗೆ ₹1,500 ಕೋಟಿ ಅನುದಾನ ಬಿಡುಗಡೆ ಮಾಡಲು ಒಪ್ಪಿಗೆ ನೀಡಿದೆ.",
                "en": "Bengaluru: Taking a significant step toward decongesting capital traffic, the Karnataka Cabinet has approved the release of ₹1,500 crore in funding for the Bengaluru Suburban Rail Project.",
                "flags": []
            },
            {
                "kn": "ಮುಖ್ಯಮಂತ್ರಿ ಸಿದ್ದರಾಮಯ್ಯ ಅವರ ಅಧ್ಯಕ್ಷತೆಯಲ್ಲಿ ಗುರುವಾರ ನಡೆದ ಸಚಿವ ಸಂಪುಟ ಸಭೆಯಲ್ಲಿ ಈ ಮಹತ್ವದ ತೀರ್ಮಾನ ತೆಗೆದುಕೊಳ್ಳಲಾಯಿತು.",
                "en": "This key decision was taken during a cabinet meeting chaired by Chief Minister Siddaramaiah on Thursday.",
                "flags": []
            },
            {
                "kn": "ಈ ಯೋಜನೆಯ ಎರಡನೇ ಹಂತದ ಕಾಮಗಾರಿ 2027ರ ವೇಳೆಗೆ ಪೂರ್ಣಗೊಳ್ಳಲಿದ್ದು, ನಿತ್ಯ 10 ಲಕ್ಷ ಪ್ರಯಾಣಿಕರಿಗೆ ಅನುಕೂಲವಾಗಲಿದೆ ಎಂದು ಮೂಲಸೌಕರ್ಯ ಅಭಿವೃದ್ಧಿ ಸಚಿವ ಎಂ. ಬಿ. ಪಾಟೀಲ್ ತಿಳಿಸಿದ್ದಾರೆ.",
                "en": "Infrastructure Development Minister M. B. Patil stated that the second phase works will be completed by 2027, benefiting 10 lakh daily commuters.",
                "flags": []
            },
            {
                "kn": "ಬೆಂಗಳೂರು ಮತ್ತು ಮೈಸೂರು ನಡುವಿನ ಸಂಪರ್ಕವನ್ನು ಸುಧಾರಿಸಲು ಹೆಚ್ಚುವರಿ 25 ರೈಲು ಬೋಗಿಗಳನ್ನು ಖರೀದಿಸಲು ಕೂಡ ಸಂಪುಟ ಅನುಮೋದಿಸಿದೆ.",
                "en": "The cabinet also sanctioned the procurement of an additional 25 train coaches to improve connectivity between Bengaluru and Mysuru.",
                "flags": []
            }
        ],
        "summary": {
            "headline_en": "Karnataka Cabinet approves ₹1,500 crore grant for Bengaluru suburban rail",
            "summary_en": "The Karnataka Cabinet chaired by Chief Minister Siddaramaiah approved ₹1,500 crore for the Bengaluru Suburban Rail Project. Phase two is slated for completion by 2027 to benefit 10 lakh daily commuters, with 25 coaches added for Bengaluru-Mysuru connectivity.",
            "key_points": [
                {"text": "Karnataka Cabinet approved ₹1,500 crore grant for suburban rail project.", "evidence": [0]},
                {"text": "Project second phase scheduled for completion by 2027, serving 10 lakh daily passengers.", "evidence": [2]},
                {"text": "Additional 25 train coaches cleared to strengthen Bengaluru-Mysuru connectivity.", "evidence": [3]}
            ],
            "key_facts": {
                "who": ["Siddaramaiah", "M. B. Patil", "Karnataka Cabinet"],
                "what": ["Suburban Rail funding release", "Coach procurement"],
                "where": ["Bengaluru", "Mysuru", "Karnataka"],
                "when": ["Thursday", "2027"],
                "numbers": ["₹1,500 crore", "10 lakh", "25"]
            },
            "verification": {
                "passed": True,
                "confidence_score": 0.98,
                "claims_checked": 3,
                "claims_supported": 3,
                "number_guard": {"status": "match", "mismatches": []},
                "entity_guard": {"status": "match", "mismatches": []}
            }
        },
        "entities": [
            {"lang": "kn", "text": "ಬೆಂಗಳೂರು", "norm_text": "Bengaluru", "type": "LOC", "sentence_idx": 0},
            {"lang": "kn", "text": "ಸಿದ್ದರಾಮಯ್ಯ", "norm_text": "Siddaramaiah", "type": "PER", "sentence_idx": 1},
            {"lang": "kn", "text": "ಎಂ. ಬಿ. ಪಾಟೀಲ್", "norm_text": "M. B. Patil", "type": "PER", "sentence_idx": 2},
            {"lang": "kn", "text": "ಮೈಸೂರು", "norm_text": "Mysuru", "type": "LOC", "sentence_idx": 3},
            {"lang": "en", "text": "Bengaluru", "norm_text": "Bengaluru", "type": "LOC", "sentence_idx": 0},
            {"lang": "en", "text": "Siddaramaiah", "norm_text": "Siddaramaiah", "type": "PER", "sentence_idx": 1},
            {"lang": "en", "text": "M. B. Patil", "norm_text": "M. B. Patil", "type": "PER", "sentence_idx": 2},
            {"lang": "en", "text": "Mysuru", "norm_text": "Mysuru", "type": "LOC", "sentence_idx": 3}
        ]
    },
    "demo-art-02": {
        "title_en": "ISRO Successfully Launches New Meteorological Satellite to Strengthen Coastal Forecasting",
        "sentences": [
            {
                "kn": "ಬೆಂಗಳೂರು: ಭಾರತೀಯ ಬಾಹ್ಯಾಕಾಶ ಸಂಶೋಧನಾ ಸಂಸ್ಥೆ (ಇಸ್ರೋ) ಶ್ರೀಹರಿಕೋಟಾದ ಸತೀಶ್ ಧವನ್ ಬಾಹ್ಯಾಕಾಶ ಕೇಂದ್ರದಿಂದ ನೂತನ ಹವಾಮಾನ ನಿಗಾ ಉಪಗ್ರಹ ಇನ್ಸಾಟ್-3ಡಿಎಸ್ ಅನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಕಕ್ಷೆಗೆ ಸೇರಿಸಿದೆ.",
                "en": "Bengaluru: The Indian Space Research Organisation (ISRO) has successfully placed the new weather monitoring satellite INSAT-3DS into orbit from the Satish Dhawan Space Centre in Sriharikota.",
                "flags": []
            },
            {
                "kn": "ಈ ಉಪಗ್ರಹವು 2,275 ಕಿಲೋಗ್ರಾಂ ತೂಕವಿದ್ದು, ಜಿಎಸ್ಎಲ್ವಿ-ಎಫ್14 ರಾಕೆಟ್ ಮೂಲಕ ನಭಕ್ಕೆ ಚಿಮ್ಮಿತು.",
                "en": "Weighing 2,275 kilograms, this satellite soared into the sky aboard the GSLV-F14 rocket.",
                "flags": []
            },
            {
                "kn": "ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ ಮತ್ತು ನೈಸರ್ಗಿಕ ವಿಕೋಪಗಳ ಮುನ್ನೆಚ್ಚರಿಕೆ ನೀಡುವಲ್ಲಿ ಈ ಉಪಗ್ರಹ ಪ್ರಮುಖ ಪಾತ್ರ ವಹಿಸಲಿದೆ ಎಂದು ಇಸ್ರೋ ಅಧ್ಯಕ್ಷ ಎಸ್. ಸೋಮನಾಥ್ ಬೆಂಗಳೂರಿನಲ್ಲಿ ಮಾಹಿತಿ ನೀಡಿದ್ದಾರೆ.",
                "en": "ISRO Chairman S. Somanath stated in Bengaluru that this satellite will play a key role in weather forecasting and disaster early warnings.",
                "flags": []
            },
            {
                "kn": "ಕರ್ನಾಟಕದ ಕರಾವಳಿ ಮತ್ತು ಮಲೆನಾಡು ಭಾಗಗಳಲ್ಲಿ ಮುಂಬರುವ ಮುಂಗಾರು ಮಳೆಯ ನಿಖರ ಮಾದರಿಗಳನ್ನು ಅಧ್ಯಯನ ಮಾಡಲು ವಿಜ್ಞಾನಿಗಳಿಗೆ ನೆರವಾಗಲಿದೆ.",
                "en": "It will assist scientists in studying accurate monsoon rain patterns across Karnataka's coastal and Malenadu regions.",
                "flags": []
            }
        ],
        "summary": {
            "headline_en": "ISRO puts 2,275 kg INSAT-3DS meteorological satellite into orbit via GSLV-F14",
            "summary_en": "ISRO launched the 2,275 kg INSAT-3DS weather satellite from Sriharikota via GSLV-F14. Chairman S. Somanath highlighted its vital role in disaster warnings and tracking monsoon precipitation across Karnataka's coastal belt.",
            "key_points": [
                {"text": "INSAT-3DS satellite successfully placed into orbit aboard GSLV-F14.", "evidence": [0, 1]},
                {"text": "Satellite weighs 2,275 kg and enhances disaster warning systems.", "evidence": [1, 2]},
                {"text": "Aids meteorological forecasting for Karnataka's coastal and Malenadu belts.", "evidence": [3]}
            ],
            "key_facts": {
                "who": ["ISRO", "S. Somanath"],
                "what": ["Satellite launch", "INSAT-3DS weather satellite"],
                "where": ["Bengaluru", "Sriharikota", "Karnataka"],
                "when": ["Recent"],
                "numbers": ["2,275 kg", "INSAT-3DS", "GSLV-F14"]
            },
            "verification": {
                "passed": True,
                "confidence_score": 0.99,
                "claims_checked": 3,
                "claims_supported": 3,
                "number_guard": {"status": "match", "mismatches": []},
                "entity_guard": {"status": "match", "mismatches": []}
            }
        },
        "entities": [
            {"lang": "kn", "text": "ಇಸ್ರೋ", "norm_text": "ISRO", "type": "ORG", "sentence_idx": 0},
            {"lang": "kn", "text": "ಶ್ರೀಹರಿಕೋಟಾ", "norm_text": "Sriharikota", "type": "LOC", "sentence_idx": 0},
            {"lang": "kn", "text": "ಎಸ್. ಸೋಮನಾಥ್", "norm_text": "S. Somanath", "type": "PER", "sentence_idx": 2},
            {"lang": "en", "text": "ISRO", "norm_text": "ISRO", "type": "ORG", "sentence_idx": 0},
            {"lang": "en", "text": "Sriharikota", "norm_text": "Sriharikota", "type": "LOC", "sentence_idx": 0},
            {"lang": "en", "text": "S. Somanath", "norm_text": "S. Somanath", "type": "PER", "sentence_idx": 2}
        ]
    },
    "demo-art-03": {
        "title_en": "Ranji Trophy: Karnataka Clinches Decisive 8-Wicket Win Against Tamil Nadu",
        "sentences": [
            {
                "kn": "ಬೆಂಗಳೂರು: ಎಂ. ಚಿನ್ನಸ್ವಾಮಿ ಕ್ರೀಡಾಂಗಣದಲ್ಲಿ ನಡೆದ ರಣಜಿ ಟ್ರೋಫಿ ಎಲೈಟ್ ಗ್ರೂಪ್ ಪಂದ್ಯದಲ್ಲಿ ಕರ್ನಾಟಕ ತಂಡವು ಸಾಂಪ್ರದಾಯಿಕ ಎದುರಾಳಿ ತಮಿಳುನಾಡು ವಿರುದ್ಧ 8 ವಿಕೆಟ್‌ಗಳ ಭರ್ಜರಿ ಗೆಲುವು ದಾಖಲಿಸಿದೆ.",
                "en": "Bengaluru: In a Ranji Trophy Elite Group clash held at the M. Chinnaswamy Stadium, Karnataka registered an 8-wicket win against rivals Tamil Nadu.",
                "flags": []
            },
            {
                "kn": "ನಾಲ್ಕನೇ ದಿನದಾಟದಲ್ಲಿ ಗೆಲುವಿಗೆ ಅಗತ್ಯವಿದ್ದ 145 ರನ್‌ಗಳ ಗುರಿಯನ್ನು ಕರ್ನಾಟಕ ಕೇವಲ 2 ವಿಕೆಟ್ ಕಳೆದುಕೊಂಡು ತಲುಪಿತು.",
                "en": "On the fourth day of play, Karnataka reached the victory target of 145 runs for the loss of just 2 wickets.",
                "flags": []
            },
            {
                "kn": "ನಾಯಕ ಮಯಾಂಕ್ ಅಗರ್ವಾಲ್ ಅಜೇಯ 78 ರನ್ ಗಳಿಸಿ ತಂಡವನ್ನು ಗೆಲುವಿನ ದಡ ಸೇರಿಸಿದರು.",
                "en": "Captain Mayank Agarwal guided the squad home with an unbeaten 78 runs.",
                "flags": []
            },
            {
                "kn": "ಬೌಲಿಂಗ್‌ನಲ್ಲಿ ವೇಗಿ ಪ್ರಸಿದ್ಧ ಕೃಷ್ಣ ಪಂದ್ಯದಲ್ಲಿ ಒಟ್ಟು 7 ವಿಕೆಟ್ ಪಡೆದು ಪಂದ್ಯಶ್ರೇಷ್ಠ ಪ್ರಶಸ್ತಿಗೆ ಭಾಜನರಾದರು.",
                "en": "With the ball, pacer Prasidh Krishna bagged a total of 7 wickets to claim the Player of the Match award.",
                "flags": []
            },
            {
                "kn": "ಈ ಗೆಲುವಿನೊಂದಿಗೆ ಕರ್ನಾಟಕ ತಂಡ ಪಾಯಿಂಟ್ ಪಟ್ಟಿಯಲ್ಲಿ ಎರಡನೇ ಸ್ಥಾನಕ್ಕೇರಿದೆ.",
                "en": "With this victory, the Karnataka side climbed to second place in the points standings.",
                "flags": []
            }
        ],
        "summary": {
            "headline_en": "Karnataka cruises to 8-wicket Ranji Trophy victory over Tamil Nadu in Bengaluru",
            "summary_en": "Karnataka defeated Tamil Nadu by 8 wickets at M. Chinnaswamy Stadium, chasing 145 runs on day four. Skipper Mayank Agarwal struck an unbeaten 78 while pacer Prasidh Krishna took 7 wickets across the match.",
            "key_points": [
                {"text": "Karnataka defeated Tamil Nadu by 8 wickets at M. Chinnaswamy Stadium.", "evidence": [0]},
                {"text": "Target of 145 achieved on day 4 for the loss of 2 wickets.", "evidence": [1]},
                {"text": "Captain Mayank Agarwal scored unbeaten 78; Prasidh Krishna named Player of the Match.", "evidence": [2, 3]}
            ],
            "key_facts": {
                "who": ["Mayank Agarwal", "Prasidh Krishna", "Karnataka team", "Tamil Nadu"],
                "what": ["Ranji Trophy victory", "Cricket match"],
                "where": ["Bengaluru", "M. Chinnaswamy Stadium"],
                "when": ["Day 4"],
                "numbers": ["8 wickets", "145 runs", "78 runs", "7 wickets"]
            },
            "verification": {
                "passed": True,
                "confidence_score": 0.99,
                "claims_checked": 3,
                "claims_supported": 3,
                "number_guard": {"status": "match", "mismatches": []},
                "entity_guard": {"status": "match", "mismatches": []}
            }
        },
        "entities": [
            {"lang": "kn", "text": "ಎಂ. ಚಿನ್ನಸ್ವಾಮಿ ಕ್ರೀಡಾಂಗಣ", "norm_text": "M. Chinnaswamy Stadium", "type": "LOC", "sentence_idx": 0},
            {"lang": "kn", "text": "ಮಯಾಂಕ್ ಅಗರ್ವಾಲ್", "norm_text": "Mayank Agarwal", "type": "PER", "sentence_idx": 2},
            {"lang": "kn", "text": "ಪ್ರಸಿದ್ಧ ಕೃಷ್ಣ", "norm_text": "Prasidh Krishna", "type": "PER", "sentence_idx": 3},
            {"lang": "en", "text": "M. Chinnaswamy Stadium", "norm_text": "M. Chinnaswamy Stadium", "type": "LOC", "sentence_idx": 0},
            {"lang": "en", "text": "Mayank Agarwal", "norm_text": "Mayank Agarwal", "type": "PER", "sentence_idx": 2},
            {"lang": "en", "text": "Prasidh Krishna", "norm_text": "Prasidh Krishna", "type": "PER", "sentence_idx": 3}
        ]
    }
}

def seed():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Categories
        category_map = {}
        for cat_data in INITIAL_CATEGORIES:
            cat = db.query(Category).filter_by(slug=cat_data["slug"]).first()
            if not cat:
                cat = Category(**cat_data)
                db.add(cat)
                db.flush()
                print(f"Added category: {cat.name_en}")
            category_map[cat.slug] = cat

        # 2. Seed Sources
        source_map = {}
        for src_data in INITIAL_SOURCES:
            src = db.query(Source).filter_by(name=src_data["name"]).first()
            if not src:
                src = Source(**src_data)
                db.add(src)
                db.flush()
                print(f"Added source: {src.name}")
            source_map[src.name] = src

        # 3. Seed Demo Articles
        demo_path = os.path.join(os.path.dirname(__file__), "demo_articles.json")
        with open(demo_path, "r", encoding="utf-8") as f:
            demo_articles = json.load(f)

        for art in demo_articles:
            art_id = art["id"]
            content_hash = hashlib.sha256(art["body_kn"].strip().encode("utf-8")).hexdigest()
            existing = db.query(Article).filter_by(content_hash=content_hash).first()
            if existing:
                print(f"Article '{art['title_kn'][:30]}...' already exists, skipping.")
                continue

            source = source_map.get(art["source_name"])
            published_dt = datetime.fromisoformat(art["published_at"].replace("Z", "+00:00"))

            article = Article(
                source_id=source.id if source else None,
                origin=art.get("origin", "dataset"),
                url=art.get("url"),
                title_kn=art["title_kn"],
                body_kn=art["body_kn"],
                content_hash=content_hash,
                section_label=art.get("section_label"),
                published_at=published_dt,
                status="ready",
            )
            db.add(article)
            db.flush()
            print(f"Created demo article ID {article.id}: {article.title_kn[:35]}...")

            # Associate category
            cat = category_map.get(art.get("section_label"))
            if cat:
                db.add(ArticleCategory(article_id=article.id, category_id=cat.id, confidence=1.0, method="ground_truth"))

            # Populate enrichment data (sentences, translations, summary, entities)
            enrichment = DEMO_ENRICHMENTS.get(art_id)
            if enrichment:
                # Add sentences
                sentence_objects = []
                for idx, sent in enumerate(enrichment["sentences"]):
                    sentence_obj = Sentence(
                        article_id=article.id,
                        idx=idx,
                        paragraph_idx=0,
                        text_kn=sent["kn"]
                    )
                    db.add(sentence_obj)
                    db.flush()
                    sentence_objects.append(sentence_obj)

                # Add translation
                translation = Translation(
                    article_id=article.id,
                    backend="indictrans2",
                    model_version="indictrans2-indic-en-1B",
                    title_en=enrichment["title_en"],
                    guard_report={"checks_passed": True, "discrepancies": []},
                    is_active=True
                )
                db.add(translation)
                db.flush()

                # Add sentence translations
                for idx, sent in enumerate(enrichment["sentences"]):
                    sent_trans = SentenceTranslation(
                        translation_id=translation.id,
                        sentence_id=sentence_objects[idx].id,
                        text_en=sent["en"],
                        labse_sim=0.92,
                        qe_score=0.95,
                        flags=sent.get("flags", [])
                    )
                    db.add(sent_trans)

                # Add summary
                summary_data = enrichment["summary"]
                summary = Summary(
                    article_id=article.id,
                    translation_id=translation.id,
                    model="gemini-2.5-flash",
                    prompt_version="summarize_v1.txt",
                    method="llm",
                    headline_en=summary_data["headline_en"],
                    summary_en=summary_data["summary_en"],
                    key_points=summary_data["key_points"],
                    key_facts=summary_data["key_facts"],
                    verification=summary_data["verification"]
                )
                db.add(summary)

                # Add entities
                for ent in enrichment.get("entities", []):
                    db.add(Entity(
                        article_id=article.id,
                        lang=ent["lang"],
                        text=ent["text"],
                        norm_text=ent.get("norm_text"),
                        type=ent["type"],
                        sentence_idx=ent.get("sentence_idx")
                    ))

        db.commit()
        print("Database successfully seeded!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()


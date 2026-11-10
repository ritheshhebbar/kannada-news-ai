# Ethics, Attribution, and Copyright Protocol

## 1. News Crawling & RSS Politeness
- **Robots.txt Adherence**: Every source listed in `sources.yaml` is checked against `robots.txt` before fetching full article pages.
- **Request Throttling**: The crawler restricts requests to at most one every 3 seconds per domain.
- **Header Identification**: User-Agent string explicitly declares: `KannadaNewsAI-ResearchBot/1.0 (+academic-research)`.
- **Paywall Protection**: Paywalled or gated content is strictly excluded.

## 2. Copyright & Fair Use
- **Original Content Redistribution**: Full copyrighted news articles are never redistributed verbatim to third parties. Only short excerpts, generated summaries, entity tags, and direct hyperlinks to the original publisher are publicly presented.
- **Attribution**: Every presented article clearly cites the original publisher name, publication timestamp, and canonical link with a "Read Original" prompt.

## 3. Disclaimers & Transparency
- **AI Labeling**: All translated sentences are explicitly badged as `Machine Translation (IndicTrans2)` and summaries are badged as `AI-Generated Summary`.
- **Honest Limitations**: Prominently notes that automated systems may make translation or nuance errors, especially regarding sensitive matters (crime, politics, judiciary), and provides a "Report Translation Error" button for human feedback.

## 4. Privacy & Data Handling
- **User Submissions**: Text submitted by users through the `/submit` endpoint is handled strictly for processing and session-based display. No user data is forwarded to external services for model training without explicit consent.
- **Session Identifiers**: Anonymous UUID session cookies are used in place of personal user tracking.

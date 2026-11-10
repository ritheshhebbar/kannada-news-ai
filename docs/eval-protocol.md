# Evaluation Protocol & Research Methodology

## 1. Research Questions
- **RQ1**: Which translation system (IndicTrans2-1B, IndicTrans2-200M, NLLB-200, Sarvam-Translate, LLM-prompted) achieves the highest translation quality on contemporary Kannada news?
- **RQ2**: Does the **Translate-Then-Summarize (P1)** pipeline outperform Summarize-Then-Translate (P2) and One-shot LLM (P3) in terms of factual faithfulness and content coverage?
- **RQ3**: Does the 7-layer verification framework reliably detect and reduce hallucinations in news summaries?
- **RQ4**: Do automated sentence-level quality estimation scores correlate with human bilingual judgment on Kannada news corpora?

## 2. Evaluation Metrics

### 2.1 Translation Quality
- **BLEU & chrF++**: Computed via `sacrebleu` with formal signatures.
- **COMET & CometKiwi**: Semantic similarity against reference translations and reference-free quality estimation.
- **MQM (Multidimensional Quality Metrics)**: Human error tagging (mistranslation, omission, addition, wrong entity, wrong number).

### 2.2 Summarization Quality & Faithfulness
- **ROUGE-1, ROUGE-2, ROUGE-L**: N-gram overlap against human reference summaries.
- **Factual Consistency / Hallucination Rate**: Ratio of summary claims unsupported by source sentences.
- **Entity & Number Precision**: Exact and normalized match percentage between summary entities/numbers and the Kannada original.

## 3. Human Annotation Guidelines
- Bilingual annotators evaluate randomized, blinded outputs.
- Sentences scored on Adequacy (1-5) and Fluency (1-5).
- Discrepancies resolved via Krippendorff's alpha agreement calibration.


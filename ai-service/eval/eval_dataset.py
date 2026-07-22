"""Fixed evaluation dataset for RAG quality tracking. Owner: Saurabh

Not a unit test - this is a manual/periodic quality check, since it makes
real Gemini calls (costs money, ~20 calls) and answer quality requires some
human judgment, not just pass/fail assertions. Run via: python eval/run_eval.py
"""

EVAL_SUBJECT_ID = "eval_fixed_subject"
EVAL_DOCUMENT_ID = "eval_fixed_doc"

# Fixed knowledge base - covers biology, physics, history, so questions can
# span topics without needing a real uploaded document.
KNOWLEDGE_BASE = [
    {"page": 1, "text": "The mitochondria is the powerhouse of the cell. It generates ATP through cellular respiration, a process that consumes oxygen and glucose."},
    {"page": 2, "text": "Photosynthesis occurs in chloroplasts. Plants convert sunlight, water, and carbon dioxide into glucose and oxygen."},
    {"page": 3, "text": "Newton's second law states that force equals mass times acceleration (F=ma). This describes how objects accelerate under applied forces."},
    {"page": 4, "text": "The speed of light in a vacuum is approximately 299,792 kilometers per second, denoted by the symbol c."},
    {"page": 5, "text": "World War II ended in 1945. The war in Europe ended in May 1945, and the war in the Pacific ended in September 1945 following Japan's surrender."},
    {"page": 6, "text": "The French Revolution began in 1789, driven by economic hardship, social inequality, and Enlightenment ideas about governance."},
    {"page": 7, "text": "DNA replication is semi-conservative, meaning each new DNA molecule contains one original strand and one newly synthesized strand."},
    {"page": 8, "text": "The water cycle includes evaporation, condensation, precipitation, and collection. Water moves continuously between the atmosphere, land, and oceans."},
]

# Each entry: question, keywords that a correct answer should contain
# (case-insensitive substring match), and which page the answer should cite.
EVAL_QUESTIONS = [
    {"question": "What does the mitochondria produce?", "expected_keywords": ["atp"], "expected_page": 1},
    {"question": "Where does photosynthesis take place?", "expected_keywords": ["chloroplast"], "expected_page": 2},
    {"question": "What is Newton's second law?", "expected_keywords": ["force", "mass", "acceleration"], "expected_page": 3},
    {"question": "How fast does light travel?", "expected_keywords": ["299,792", "kilometers"], "expected_page": 4},
    {"question": "When did World War II end?", "expected_keywords": ["1945"], "expected_page": 5},
    {"question": "What caused the French Revolution?", "expected_keywords": ["inequality", "enlightenment"], "expected_page": 6},
    {"question": "What does semi-conservative mean in DNA replication?", "expected_keywords": ["one original", "new"], "expected_page": 7},
    {"question": "What are the stages of the water cycle?", "expected_keywords": ["evaporation", "condensation", "precipitation"], "expected_page": 8},
    {"question": "What gas do plants release during photosynthesis?", "expected_keywords": ["oxygen"], "expected_page": 2},
    {"question": "What year did the French Revolution begin?", "expected_keywords": ["1789"], "expected_page": 6},
    # Adversarial: question with no answer in the knowledge base - model
    # should say it doesn't know, not hallucinate.
    {"question": "What is the capital of Australia?", "expected_keywords": ["don't", "cannot", "not contain", "no information", "couldn't find", "does not contain"], "expected_page": None},
    {"question": "Who invented the telephone?", "expected_keywords": ["don't", "cannot", "not contain", "no information", "couldn't find", "does not contain"], "expected_page": None},
]
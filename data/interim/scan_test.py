import pandas as pd, spacy
from src.s3_ner import GRADE_PATTERNS, MEASUREMENT_PATTERNS, load_relevant_corpus

df = load_relevant_corpus()
nlp = spacy.load('en_core_web_sm')
r = nlp.add_pipe('entity_ruler', before='ner')
r.add_patterns(GRADE_PATTERNS + MEASUREMENT_PATTERNS)

vals = set()
for t in df['text']:
    if isinstance(t, str):
        for e in nlp(t).ents:
            if e.label_ in ('CORE_LOSS', 'SI_CONTENT', 'MPA_VALUE', 'FLUX_DENSITY'):
                vals.add((e.label_, e.text))

for v in sorted(vals):
    print(v)
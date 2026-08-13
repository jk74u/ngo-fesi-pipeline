import spacy
import pandas as pd
import re
from src.config import DATA_PROCESSED, SPACY_MODEL, GAZETTEER_DIR, GAZETTEER_FILES

GRADE_PATTERNS = [
    #JIS family (single token)
    {"label": "GRADE", "pattern": [{"TEXT": {"REGEX": r"^\d{2}A\d{3,4}$"}}]},
    # EN family (multi token)
    {"label": "GRADE", "pattern": [
    {"TEXT": {"REGEX": r"^M\d{3}$"}},        # token 1: M300
    {"TEXT": "-"},                            # token 2: the hyphen
    {"TEXT": {"REGEX": r"^\d{2}A\d?$"}},      # token 3: 35A or 35A5
]},
#Nippon family (single token)
{"label": "GRADE", "pattern": [{"TEXT": {"REGEX": r"^\d{2}H[A-Z]{0,2}\d{3,4}[A-Z]?$"}}]},
#JFE family (single token)
{"label": "GRADE", "pattern": [{"TEXT": {"REGEX": r"^\d{2}JNE\d{3}$"}}]},
# Cogent single-token form: NO20
{"label": "GRADE", "pattern": [{"TEXT": {"REGEX": r"^NO\d{2}$"}}]},
# Cogent hyphenated form: NO30-1600 (multi-token)
{"label": "GRADE", "pattern": [
    {"TEXT": {"REGEX": r"^NO\d{2}$"}},
    {"TEXT": "-"},
    {"TEXT": {"REGEX": r"^\d{3,4}$"}},
]},

    ]
    #TIER 1 measurement patterns
MEASUREMENT_PATTERNS = [ 
    {"label": "CORE_LOSS", "pattern": [{"TEXT": {"REGEX": r"^W\d+(\.\d+)?/\d+k?$"}}]},
    {"label": "CORE_LOSS", "pattern": [
    {"TEXT": {"REGEX": r"^\d+(\.\d+)?$"}},   # 2.3  (number, optional decimal)
    {"TEXT": "W"},                            # W
    {"TEXT": "/"},                            # /
    {"TEXT":"kg"},                # kg  (lowercased match, safe against Kg/KG)
]},
#Silicon content patterns
{"label": "SI_CONTENT", "pattern": [
    {"TEXT": {"REGEX": r"^[0-6](\.\d+)?$"}},   # 0–6.x, excludes 75, 100, 9
    {"TEXT": {"IN": ["%", "mass%", "wt%"]}},          # %, mass%, or wt%
    {"LOWER": {"IN": ["si", "silicon"]}},             # Si or silicon
]},
#STRENGTH YIELD patterns
{"label": "MPA_VALUE", "pattern": [
    {"TEXT": {"REGEX": r"^\d+(\.\d+)?$"}},   # 690, 841
    {"TEXT": "MPa"},                          # MPa
]},
#FLux density patterns
# B-notation form: B50, B8
{"label": "FLUX_DENSITY", "pattern": [{"TEXT": {"REGEX": r"^B(8|10|25|50|80)$"}}]},
# Tesla form: 1.5 T
{"label": "FLUX_DENSITY", "pattern": [
    {"TEXT": {"REGEX": r"^[0-2](\.\d+)?$"}},   # 0, 1, 2, or 0.x / 1.x / 2.x
    {"TEXT": "T"},
]},
]

#Context scoping ensuring terms belong to Ngo or GO
NGO_TRIGGERS = [
    r"\bnon-oriented\b",
    r"\bnon-grain-oriented\b",
    r"\bngo\b"
]

COMPETITOR_LABELS= {"COMPETING_MATERIAL", "OOS_GRADE"}

TARGET_LABELS = {
        "GRADE", "CORE_LOSS", "SI_CONTENT",
        "MPA_VALUE", "FLUX_DENSITY"
    }

def load_relevant_corpus():
    
    #Load the relevant corpus from the processed data directory.
    #Returns a pandas DataFrame containing the relevant documents.
    
    corpus_path = DATA_PROCESSED / "corpus_filtered.csv"
    if not corpus_path.exists():
        raise FileNotFoundError(f"Relevant corpus file not found at {corpus_path}")
    
    df = pd.read_csv(corpus_path)
    relevant_df = df[df['is_relevant'] == True].copy()

    return relevant_df

def preview_entities(df, nlp, num_docs=2):
    #Testing the NER model on a few documents from the relevant corpus.
    #Prints the entities found in the first few documents.
    sample_df = df.head(num_docs)
    for _, row in sample_df.iterrows():
        text = row['text']

        if not isinstance(text, str):
            print(f"Skipping non-string text: {text}")
            continue

        doc = nlp(text)
        doc_name = row.get('source_path',row.get('doc_id', 'Unknown'))
        print(f"\n------Previewing Document: {doc_name}------")
        print("note expect junk and some noise where the nlp has done some entity recognition")
        for ent in doc.ents:
            print(f"Label: {ent.label_: <15}, Text: {ent.text}")

def run_piece_1():
    # Load the relevant corpus
    relevant_df = load_relevant_corpus()
    print(f"Loaded {len(relevant_df)} relevant documents from the corpus.")
    # Load the spaCy model
    print(f"Loading spaCy model: {SPACY_MODEL}...")
    nlp = spacy.load(SPACY_MODEL)
    print(f"Loaded spaCy model: {SPACY_MODEL}")
    # Preview entities in the first few documents
    preview_entities(relevant_df, nlp, num_docs=2)

def run_piece_2():
    # Load the relevant corpus
    relevant_df = load_relevant_corpus()
    print(f"Loaded {len(relevant_df)} relevant documents from the corpus.")
    # Load the spaCy model
    print(f"Loading spaCy model: {SPACY_MODEL}...")
    nlp = spacy.load(SPACY_MODEL)
    print(f"Loaded spaCy model: {SPACY_MODEL}")
    # Add custom patterns to the NER model
    ruler = nlp.add_pipe("entity_ruler", before="ner")
    ruler.add_patterns(GRADE_PATTERNS)
    ruler.add_patterns(MEASUREMENT_PATTERNS)
    #adding regex patterns
    ruler.add_patterns(load_gazetteer_patterns())
    print("Added custom grade ,measurements and gazetteer patterns to the NER model.")
    # Preview entities in the first few documents
    preview_entities(relevant_df, nlp, num_docs=2)

def load_gazetteer_patterns():
    all_patterns= []
    print("Loading gazetteer patterns from files...")
    for filename, label in GAZETTEER_FILES.items():
        filepath = GAZETTEER_DIR / filename
        #Faliure to find file warning
        if not filepath.exists():
            print(f"Warning: Gazeteer file missing - {filepath}")
            continue

        term_count = 0
#Encoding critical to maintain special symbol terms
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                term = line.strip()
                if term:
                    #skips blank lines
                    all_patterns.append({"label": label, "pattern": term})
                    term_count += 1
        print(f"{label: <20}: {term_count: >3} terms loaded from {filename}")
    print(f"total gazetteer patterns loaded: {len(all_patterns)}")
    print("------------------------------------------------\n")

    return all_patterns
#SCOPE TAG evaluates whther a sentence around an entity has values which categorise it as NGO or another
def scope_tag(ent, doc):
#Sentence grabbing
    sent = ent.sent
    sent_text_lower = sent.text.lower()

    #Checking sentence for NGo values
    has_ngo = any(re.search(pattern, sent_text_lower) for pattern in NGO_TRIGGERS)
    #status for any competitor or OOS/GO steel
    has_competitor = False

    for other_ent in doc.ents:
        #checks if entities are withina sentence length first
        if other_ent.start_char >= sent.start_char and other_ent.end_char <= sent.end_char:
            #check if it has competitor or GO/OOs word in "sentence"
            if other_ent.label_ in COMPETITOR_LABELS:
                #Ensure not matching the entity agaisnt itself
                if other_ent != ent:
                    has_competitor = True
                    break # if it does stop the program

# Assigning context label
#runs through scenarios and results( reminds me of a joke in undergrad just if statement allscenarios and its AI bro)
    if has_competitor and not has_ngo:
        return "COMPETITOR"
    elif has_ngo and not has_competitor:
        return "NGO"
    elif has_ngo and has_competitor:
        return "AMBIGUOUS"
    else: 
        return "UNSPECIFIED"

def extract_scoped_entities(df, nlp):
    #Applying the context scoping onto the tier1 entities MEAsurements and grades.
    records = []
    # only applying these to priority info  for instance the tier 1 mentioned
   

    for _, row in df.iterrows():
        text = row['text']
        doc_id = row.get('doc_id','Unknown')

        if not isinstance(text, str):
            continue
        doc = nlp(text)

        for ent in doc.ents:
            if ent.label_ in TARGET_LABELS:
                #actual scope taggin logiv
                scope = scope_tag(ent,doc)
                context_sentence = ent.sent.text.strip()

                #Bundled into combined record
                records.append({
                    "doc_id": doc_id,
                    "text": ent.text,
                    "label": ent.label_,
                    "scope_tag": scope,
                    "context": context_sentence
                })
    return records

if __name__ == "__main__":
    run_piece_2()

import spacy
import pandas as pd
from src.config import DATA_PROCESSED, SPACY_MODEL

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

if __name__ == "__main__":
    run_piece_1()

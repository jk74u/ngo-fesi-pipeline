#boilerplate feature is to be implemented later if headings have an affect oc clustering results etc.
import pandas as pd
from src.config import DATA_PROCESSED, DOMAIN_TERMS, RELEVANCE_THRESHOLD
from pathlib import Path

def load_corpus():
    """
    Load the processed corpus from a CSV file.

    Returns:
        pd.DataFrame: DataFrame containing the processed corpus.
    """
    corpus_path = DATA_PROCESSED / "corpus.csv"
    return pd.read_csv(corpus_path)
#Document scoring function based on the number of domain terms present in the text.
def count_domain_terms(text):
    #First checking if there is a text to process.
    if not isinstance(text, str):
        return 0
#lowercasing all text so that case sensitivities does not affect the search
    text_lower = text.lower()
    match_count = 0
#Iterating through the domain terms and counting how many of them are present in the text.
    for term in DOMAIN_TERMS:
        if term.lower() in text_lower:
            match_count += 1
#returning the number of domain terms found in the text.
    return match_count
#RELEVANCE ASSESMENT FUNCTION
def assess_relevance(text):
    count = count_domain_terms(text)
    is_relevant = count >= RELEVANCE_THRESHOLD
    return is_relevant, count
#RELEVANCE TAGGING FUNCTION
def build_filtered():
    df = load_corpus()
    results = df['text'].apply(assess_relevance)
    #ADDING 2 new columns TO THE DATAFRAME
    df['is_relevant'] = [res[0] for res in results]
    df['domain_term_hits'] = [res[1] for res in results]

    relevant_count = df['is_relevant'].sum()
    total_count = len(df)
    print(f"\n---------------- Relevance Assessment Summary ----------------\n")
    print(f"Total documents: {total_count}")
    print(f"Relevant documents: {relevant_count}")
    print(f"Not relevant documents: {total_count - relevant_count}")
    print("-------------------------------------------------------------\n")

    print("---VALIDATING RELEVANCE ASSESSMENT FUNCTION---")

    for _, row in df.iterrows():
        #if filename not found then doc id will be shown.
        filename = Path(row['source_path']).name if pd.notna(row.get('source_path')) else row['doc_id']
        status = "KEEP" if row['is_relevant'] else "DROP"
        # Using string formatting to align the columns nicely for scanning
        print(f"[{status}] Hits: {row['domain_term_hits']:02d} | {filename}")
#Save new filtered data to DATA_PROCESSED directory
    output_path = DATA_PROCESSED / "corpus_filtered.csv"
    df.to_csv(output_path, index=False)
    print(f"\nFiltered corpus saved to: {output_path}\n")

    return df

if __name__ == "__main__":
    build_filtered()
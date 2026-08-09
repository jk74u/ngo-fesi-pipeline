import pandas as pd 
import fitz 
import re
import datetime
import hashlib
from pathlib import Path
from src.config import DATA_RAW, DATA_PROCESSED

def build_year_lookup(zotero_csv_path, manual_years_csv_path):

    year_lookup = {}
#REading in Zotero export CSV to build a lookup of filename to publication year. The Zotero export is expected to have columns 'File Attachments' and 'Publication Year'. We drop any rows where 'File Attachments' or 'Publication Year' is NaN, as those entries are not useful for our lookup.   
    zotero_df = pd.read_csv(zotero_csv_path)
    zotero_valid = zotero_df.dropna(subset=['File Attachments', 'Publication Year'])

# scans Zoetero export for files with valid publication years and builds a lookup dictionary of filename to year. Also reads in manual_years.csv to add any additional mappings.
    for index, row in zotero_valid.iterrows():
        filename = Path(row['File Attachments']).name
        year_lookup[filename] = row['Publication Year']


# Read manual year mappings
    manual_df = pd.read_csv(manual_years_csv_path)

    for index, row in manual_df.iterrows():
        year_lookup[row['filename']] = row['year']

    return year_lookup

def extract_text(pdf_path):
    #core logic seperated as it is reusable.
    #Light cleaning of the text with PyMuPDF of only whitespaces

    try:
        with fitz.open(pdf_path) as doc:
            text_parts = [page.get_text() for page in doc]
        raw_text = " ".join(text_parts)

        cleaned_text = re.sub(r'\s+', ' ', raw_text).strip()

        return cleaned_text

    except Exception as e:
       # any errors in reading the PDF will be logged and the function will return None enduring that 
       # one bad PDF does not halt the entire processing pipeline.
        print(f"Error reading {pdf_path}: {e}")
        return None

def assemble_canonical_row(pdf_path, year_lookup, missing_years_list, doc_id=None):
    pdf_path = Path(pdf_path)
    filename = pdf_path.name
#if doc_id is not provided, generate a unique doc_id using the MD5 hash of the PDF path. This ensures that each document has a unique identifier based on its file path.

    if doc_id is None:
        doc_id = hashlib.md5(str(pdf_path).encode()).hexdigest()

    text = extract_text(pdf_path)
    year = year_lookup.get(filename)
    if pd.isna(year) or year is None:
        print(f"Year not found for {filename}. Adding to missing_years_list.")
        missing_years_list.append(filename)
        year = None
    else:
        year = int(year)

    row = {"doc_id": doc_id,
        "source_path": str(pdf_path),
        "text": text,
        "year": year,
        "source_type": "paper",          # constant this batch
        "text_source": "fulltext",       # constant this batch
        "origin": "local_pdf_zotero",    # identifies this adapter
        "title": None,                   # leave blank for now
        "doi": None,                     # leave blank for now
        "ingest_date": datetime.date.today().isoformat()
    }
    return row

#COPUS FINAL BOSS
def build_corpus():
    zotero_csv = DATA_RAW / "zotero_export.csv"
    manual_years_csv = DATA_RAW / "manual_years.csv"
    year_lookup = build_year_lookup(zotero_csv, manual_years_csv)

    rows = []
    missing_years_list = []
    failed_extractions = 0

    pdf_files = list(DATA_RAW.glob("*.pdf"))

    for i, pdf_path in enumerate(pdf_files):

        row = assemble_canonical_row(
            pdf_path=pdf_path,
            year_lookup=year_lookup, 
            missing_years_list=missing_years_list, 
            doc_id=i

                )
        if row["text"] is None:
            failed_extractions += 1
                
        rows.append(row)
    #Pandas DataFrame creation from the list of rows. 
    corpus_df = pd.DataFrame(rows)

    total_pdfs = len(pdf_files)
    successful_extractions = total_pdfs - failed_extractions

    print(f"\n----INGESTION SUMMARY----")
    print(f"Total PDFs processed: {total_pdfs}")
    print(f"Successful extractions: {successful_extractions}")
    print(f"Failed extractions: {failed_extractions}")
    print(f"Missing publication years for {len(missing_years_list)} PDFs. See missing_years_list for details.")

    if missing_years_list:
        print(f"\nMissing publication years for the following PDFs:")
        for missing in missing_years_list:
            print(f"- {missing}")
    print("-----------------------------\n")

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    output_path = DATA_PROCESSED / "corpus.csv"
    corpus_df.to_csv(output_path, index=False)
    print(f"Corpus saved to {output_path}")
    return corpus_df

if __name__ == "__main__":
    build_corpus()
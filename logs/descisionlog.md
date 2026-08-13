DevelopmentLog: Dissertation project of textual extraction and modelling of NGO info

7/8/26: Corpus assembly for NGO steel from 2006-2026 (adjustable) into 5 year time periods (adjustable). For now we would go for these numbers to start programming but making them adjustable helps if better time framing or analysis gap is required. 

Goal: For now we will build and develop corpus and then test it on the research papers we have gathered from out literature review as a test of the system working

Problems:

Next step: hopefully if this system works expanding the inputs through automated or manual means is another task entirely 

AI use: Claude structured what a build for this pipeline may look like i have discussed and traded ideas onto what are reasonable goals for today before it helps me with the coding process.
Concluding update: SETUP complete config setup corpus still needs building .

8/8/26: 40 pdf test passed.
core corpus logic completed tes was don with a temporary zotero csv to gather metadata but text extraction worked well with a slight test on tables which ran ok not guarnteed to always however.

10 attribute row decided each pdf has its own hashed id every stage having a clear error handaling and debugging setup with processed failed readings or missing information 

every stage was built so it was inspectable by me and checked that it gave a readable output searches pritns of text to read etc. 

system is built that every stage could be reused or replaced with a new tool e.g for now zotero metadata fro the pdfs we have however will have to eb replaced when automated new pdfs are handaled thorugh an api that does it as the source comes through.

validation of cross checking the actual pdfs against a zoetero record to encure ther was no missing files 

Problems: some text names were not consistent across actual pdf and zotero metadata. plus some pdf were missing its metadata that had to be handled mannually (short unwanted fix).
table data is flattend in order yes but falttened. will have to fix later stages of pipeline
Ai use: intructional guidance on how to code in desgin and discussion on the overall design of teh system including the way forward in building each section.
11/8/26
Built s2_filter.py — coarse document-level filter tagging each doc is_relevant + domain_term_hits, reading corpus.csv, writing corpus_filtered.csv. Tags, doesn't delete (full corpus retained; dropped papers recoverable).
Method: case-insensitive count of distinct DOMAIN_TERMS (27 terms, tiered by identity/property/structure/application) against RELEVANCE_THRESHOLD, both in config.py.
Threshold set empirically to 8, not pre-chosen — the hit-count distribution was clearly bimodal (domain papers mostly 10–25, ML/method papers 0–5), and 8 sits in the gap between the two populations. Rejected 5 (let method-adjacent papers leak in) and 10 (dropped genuine papers without solving the real issue).
Validated against known corpus: cleanly separates ~14 steel-domain papers from ML/NLP method papers (Blei, BERTopic, Sentence-BERT, Weston, etc. all correctly dropped).
Known limitation (logged honestly): frequency-counting measures vocabulary-density, not topical focus — so vocabulary-dense market/demand papers (Bauer 21, Lucchini 19) pass despite being market-side not materials-side. No threshold cleanly removes them; decision is to separate them at the clustering stage rather than distort the filter.
De Almeida (8, borderline transformer-regulation paper) — [note whichever you decided: kept as application-context / flagged borderline].
Rejected alternative: embedding-similarity filtering — deferred to Pass 2 as more robust but less transparent.
12/8/26: 
spaCy pipeline established; pretrained NER (Tier 3) confirmed working on filtered corpus — catches producers (ORG) and geography (GPE); heavy noise on units/table-numbers/citations observed, confirming the need for Tier-1 regex and Tier-2 gazetteers to handle domain entities the general model mishandles.
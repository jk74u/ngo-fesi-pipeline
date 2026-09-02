NLP extraction Pipeline on NGO Electric steel literature
7 stage pipeline staring from Stage 1: corpus. Stage 2: filtering stage 3: NER stage 4: normalisation stage 5: slustering stage 6: temporal visualisations stage 7: cost bridge and calculated values.

STEP1: setup run these commands
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
STEP2 : ensure sources populate the data / raw file
results published to data / processed

STEP3 run commands for each stage:
python -m src.s1_corpus
python -m src.s2_filter
python -m src.s3_ner
python -m src.s4_norm
python -m src.s5_cluster
python -m src.s6_time
python -m src.s7_bridge
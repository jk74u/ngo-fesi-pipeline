from pathlib import Path
#.parent-./src .parent.parent->root(ngo-fesi-pipeline)
ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_INTERIM = ROOT / "data" / "interim"
OUTPUTS = ROOT / "outputs"
TOPIC = "non-grain-oriented FeSi electrical steels" 
#for now, we will focus on this topic only. In future, we can add more topics and make it dynamic. 
#FILTERING PARAMETERS (#core, properties, structure ,applications)
DOMAIN_TERMS = [
    "non-oriented", "non-grain-oriented", "NGO", "NOES", "electrical steel",
    "silicon steel", "FeSi", "Fe-Si", "lamination steel", "soft magnetic",
    "core loss", "iron loss", "magnetic flux density", "permeability",
    "coercivity", "hysteresis", "eddy current", "magnetostriction",
    "grain", "texture", "annealing", "crystalline", "alloy",
    "motor", "transformer", "rotor", "stator", "traction",
]
RELEVANCE_THRESHOLD = 8
#TUNABLE TIME PARAMETERS
START_YEAR = 2006
END_YEAR = 2026
BUCKET_YEARS = 5
#MODEL NAMES
SPACY_MODEL = "en_core_web_sm"
EMBED_MODEL = "all-MiniLM-L6-v2"
GAZETTEER_PATH = DATA_RAW / "gazetteer.txt" 
import pandas as pd
import re
from src.config import DATA_PROCESSED

KEEP_LABELS = {
    "GRADE", "CORE_LOSS", "SI_CONTENT", "MPA_VALUE", "FLUX_DENSITY",
    "APPLICATION", "COMPETING_MATERIAL", "PRODUCER", "PROCESSING",
    "GRADE_BRAND", "STANDARD", "TEST_METHOD", "OOS_GRADE",
}

VALUE_LABELS = {"CORE_LOSS", "SI_CONTENT", "MPA_VALUE", "FLUX_DENSITY"}

UNIT_BY_LABEL = {
    "CORE_LOSS": "W/kg",
    "SI_CONTENT": "%",
    "MPA_VALUE": "MPa",
    "FLUX_DENSITY": "T",
}

PROPERTY_BOUNDS = {
    "yield_strength": (180, 900),
    "tensile_strength": (300, 950),
    "applied_stress": (0, 400),
}

def load_entities():
    entities_path = DATA_PROCESSED / "entities.csv"
    if not entities_path.exists():
        raise FileNotFoundError(f"Entities file not found at {entities_path}. Run Stage 3 or open folder")
    return pd.read_csv(entities_path)

def filter_entities(df):

    #essentially drops the default SpaCY labels and keeps teh custom  built ones
    filtered_df = df[df['label'].isin(KEEP_LABELS)].copy()
    return filtered_df
#This seperates the unit from the numeric value
def parse_value(entity_text, label):
    #checks if value is numeric first
    if label not in VALUE_LABELS:
        return (None, None)
    #checks is the value is a type of notation not standard unit
    if re.match(r'^[WB]\d', entity_text):
        return (None, "notation")
    #parses the leading number
    match = re.match(r'^([\d.]+)', entity_text)
    if not match:
        return(None,None)

    try:
        value = float(match.group(1))
    except ValueError:
        # failsafe for numbers which arent extracted right
        return(None,None)
    # assign set unit according to label
    unit = UNIT_BY_LABEL[label]

    return (value, unit)

def canonicalise(entity_text, value_numeric, unit):
    # value entities: build a clean standardised string from the parsed parts
    if pd.notna(value_numeric) and unit not in (None, "notation"):
        return f"{value_numeric} {unit}"
    # everything else: keep original text as-is (grades/terms canonicalised later)
    return entity_text

def resolve_property(context, label):
    # organising context for MPA values
    if label != "MPA_VALUE":
        return None
    # if context is missing
    if not isinstance(context, str):
        return "unspecified"

    text = context.lower()

    # THE BIG ARGUEMENT LADDER
    if "yield" in text:
        return "yield_strength"
    if "tensile" in text and "strength" in text:
        return "tensile_strength"
    if ("applied" in text or "residual" in text or "compressive" in text or "tensile" in text) and "stress" in text:
        return "applied_stress"
    # standalone load-type words even without "stress"
    if "tension" in text or "compression" in text or "compressive" in text:
        return "applied_stress"
    if "strength" in text:
        return "unspecified"
    return "unspecified"

def validate(value_numeric, resolved_property):
    #checks if the value is numeric first
    if pd.isna(value_numeric) or resolved_property in (None, "unspecified"):
        return ""
    
    bounds = PROPERTY_BOUNDS.get(resolved_property)
    if bounds is None:
        return ""
    low, high = bounds
    if value_numeric < low or value_numeric > high:
        return "out_of_range"
    return ""

def run_stage4():

    print("\n=== STAGE 4: NORMALISATION ===")

    df = load_entities()
    before = len(df)

    filtered = filter_entities(df)
    after = len(filtered)

    #parse_value call up
    filtered[['value_numeric', 'unit']] = filtered.apply(
        lambda row: pd.Series(parse_value(row['entity_text'], row['label'])),
        axis=1)
    # canonlicalisation
    filtered['canonical_form'] = filtered.apply(
        lambda row: canonicalise(row['entity_text'], row['value_numeric'], row['unit']),
        axis=1
)
    filtered['resolved_property'] = filtered.apply(
        lambda row: resolve_property(row['context'], row['label']), 
        axis=1
    )

    filtered['review_flag'] = filtered.apply(
        lambda row: validate(row['value_numeric'], row['resolved_property']),
        axis=1
)

    #Printed report
    print(f"Entities before filter: {before}")
    print(f"Entities after filter: {after}")
    print(f"Dropped {before - after} generic entities.\n")
    
    
    
    print("Survivng labels count:")
    print(filtered['label'].value_counts().to_string())

    print("\nParsed value sample (value entities):")
    print(filtered[filtered['value_numeric'].notna()][['entity_text', 'label', 'value_numeric', 'unit']].head(10).to_string(index=False))

    print("\nCanonical form sample (mixed labels):")
    sample = filtered.groupby('label').head(2)[['entity_text', 'label', 'canonical_form']]
    print(sample.head(20).to_string(index=False))
#MPa context 
    print("\nMPa property resolution (all values):")
    mpa = filtered[filtered['label'] == 'MPA_VALUE']
    if not mpa.empty:
        # Using to_string(index=False) gives a clean table view in the terminal
        print(mpa[['entity_text', 'resolved_property', 'context']].to_string(index=False))
    else:
        print("No MPA_VALUE entities found to resolve.")
#bounds check
    flagged = filtered[filtered['review_flag'] != ""]
    print(f"\nValues flagged for review: {len(flagged)}")
    if not flagged.empty:
        print(flagged[['entity_text', 'resolved_property', 'value_numeric', 'review_flag']].to_string(index=False))
#Saving file
    output_path = DATA_PROCESSED / "entities_normalised.csv"
    filtered.to_csv(output_path, index=False)
    print(f"\nStage 4 complete. Saved normalised entities to: {output_path}")


if __name__ == "__main__": 
    run_stage4()

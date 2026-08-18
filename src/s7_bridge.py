import pandas as pd
import re
from src.config import DATA_PROCESSED

def parse_thickness(grade_text):
    # inferring steel thickness from grade names etc
    if not isinstance(grade_text, str):
        return None
    
    grade_text = grade_text.upper().strip()

    #En family
    en_match = re.search(r'M\d{3}-(\d{2})A', grade_text)
    if en_match:
        return float(en_match.group(1)) / 100.0
    # Cogent
    no_match = re.search(r'^NO(\d{2})' , grade_text)
    if no_match:
        return float(no_match.group(1)) / 100.0
    #JIS , Nippon, JFE 
    prefix_match = re.search(r'^(\d{2})[A-Z]' , grade_text)
    if prefix_match:
        return float(prefix_match.group(1)) / 100.0

    return None

def iron_sheet_price(thickness):
    # using Hemsen's(2023) formulae for ngo steel thickness based on 0.35 mm = 1 euro/kg
    if pd.isna(thickness) or thickness is None or thickness <= 0:
        return None
    
    relative_price = (1.0 * 0.35) / thickness

    return round(relative_price , 3)

def assign_cost_role(label):
    # maps the NER labels into roles for  a full cost model, id it is implemented
    roles = {
        "GRADE": "material_cost_input",
        "GRADE_BRAND": "material_cost_input",
        "CORE_LOSS": "loss_cost_input",
        "SI_CONTENT": "material_property",
        "PROCESSING": "manufacturing_cost_input",
        "APPLICATION": "model_selector",
        "FLUX_DENSITY": "loss_parameter"

    }
    return roles.get(label, "") # this whole function is to ensure the ability of future expansion and future work is easy.

def build_bridge_table(df):
    # this created a dataframe structure ready to be ingested by a cost model if built

    # Assigning cost model roles 
    df['cost_role'] = df['label'].apply(assign_cost_role)

    # filter top only show rows that have a cost model role 
    bridge_df = df[df['cost_role'] != ""].copy()

    # adding new columnns
    bridge_df['thickness_mm'] = None
    bridge_df['relative_price_eur_kg'] = None

    #extracting the thickness from grades and processing them for cost
    grade_mask = bridge_df['label'].isin(['GRADE', 'GRADE_BRAND'])

    bridge_df.loc[grade_mask, 'thickness_mm'] = bridge_df.loc[grade_mask, 'entity_text'].apply(parse_thickness)
    bridge_df.loc[grade_mask, 'relative_price_eur_kg'] = bridge_df.loc[grade_mask, 'thickness_mm'].apply(iron_sheet_price)

    # ordering the columns 
    expected_cols = ['doc_id', 'entity_text', 'label', 'value_numeric', 'unit',
                    'scope_tag', 'resolved_property', 'cost_role', 'thickness_mm', 'relative_price_eur_kg']
    # validating that all columns are presented in the way above
    final_cols = [col for col in expected_cols if col in bridge_df.columns]

    return bridge_df[final_cols]

def run_stage7():
    # calls the functions and prints the results for display
    print("\n=== Stage 7: Cost Model (data prep(bridge)) ===")

    input_path = DATA_PROCESSED / "entities_normalised.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Missing {input_path}. please run stage 4 first")

    df = pd.read_csv(input_path)

    #bridge construction
    bridge_df = build_bridge_table(df)

    # THe report
    print("\n---- Cost bridge report ----")

    # distribution of the cost model roles
    print("Parameters mapped to cost model roles:")
    print(bridge_df['cost_role'].value_counts().to_string())

    # displaying the grades parsed for thickness values
    grades_total = len(bridge_df[bridge_df['label'].isin(['GRADE', 'GRADE_BRAND'])])
    grades_parsed = bridge_df['thickness_mm'].notna().sum()
    print(f"\nThickness Parsing REcall: {grades_parsed}/{grades_total} grades sucessfully parsed")

    #Price range
    if grades_parsed > 0:
        min_price = bridge_df['relative_price_eur_kg'].min()
        max_price = bridge_df['relative_price_eur_kg'].max()
        print(f"Computed relative price range: {min_price} to {max_price} (eur/Kg)")

        #SAMple testing the bridge
        print("\nSample Grade -> Thickness -> Price mappings:")
        sample = bridge_df[bridge_df["thickness_mm"].notna()][['entity_text', 'thickness_mm', 'relative_price_eur_kg']].drop_duplicates().head(5)
    
    output_path = DATA_PROCESSED / "cost_bridge.csv"
    bridge_df.to_csv(output_path, index=False)
    print(f"\n=== Stage 7 Complete saved to {output_path.name} ===")

if __name__ == "__main__":
    run_stage7()



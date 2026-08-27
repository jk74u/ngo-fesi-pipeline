import pandas as pd
import re
from src.config import DATA_PROCESSED
from adjustText import adjust_text
import matplotlib.pyplot as plt
import numpy as np


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
def plot_cost_curve(bridge_df):
    # pulling the grades tha gave a thickness
    grades = bridge_df[bridge_df['thickness_mm'].notna()]
    x = grades['thickness_mm']
    y = grades['relative_price_eur_kg']

    fig, ax = plt.subplots(figsize=(9,6))

    # equation from hemsen plotted as a smooth curve
    d = np.linspace(x.min() * 0.9, x.max() * 1.1, 200)
    k = 0.35 / d
    ax.plot(d, k, color='grey', linestyle='--', label='Hemsen: k = 0.35 / d')

    ax.scatter(x,y, color='tab:red', alpha=0.6, s=40, label='Extracted grades')
    #annotating grades plotted 
    
    to_label = grades.sort_values('thickness_mm').drop_duplicates('thickness_mm')
    #counts number of grades and shows one example
    label_data = (grades.groupby('thickness_mm')
                        .agg(n_grades=('entity_text', 'size'),
                            example=('entity_text', 'first'),
                            price=('relative_price_eur_kg', 'first'))
                        .reset_index())
    print("COLUMNS:", label_data.columns.tolist())
    print(label_data.head())
    texts = []
    
    for _, r in label_data.iterrows():
        label = f"{r['n_grades']} grades, e.g. {r['example']}"
        texts.append(ax.text(r['thickness_mm'], r['price'], label, fontsize=7))
    adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='-', color='grey', lw=0.4))
        #ax.annotate(name, (xi, yi), fontsize=6, rotation=45, ha='left', va='bottom', xytext=(2,2), textcoords='offset points')

    stats_text = (
        f"n = {len(grades)} grades\n"
        f"Thickness: {grades['thickness_mm'].nunique()}\n"
        f"Price range: {y.min():.2f}-{y.max():.2f} Eur/Kg\n"
        f"Mean price: {y.mean():.2f} Eur/Kg\n"
        f"Median: {y.median():.2f} Eur/Kg\n"
        f"Std dev: {y.std():.2f}"
    )
    ax.text(0.78, 0.78, stats_text, transform=ax.transAxes,
            fontsize=8, va='center',
            bbox=dict(boxstyle='round', facecolor='whitesmoke', edgecolor='grey'))


    ax.set_xlabel("Sheet thickness (mm)")
    ax.set_ylabel("Relative price (Eur/Kg)")
    ax.set_title("Extracted Grade thickness against Hemsens price equation(k=0.35/d)")
    ax.legend()
    plt.tight_layout()

    outpath = DATA_PROCESSED / "cost_thickness_curve.png"
    plt.savefig(outpath, dpi=120)
    plt.close()
    print(f"Saved cost curve to: {outpath.name}")
def plot_thickness_distribution(bridge_df):
    #pulling grades that provide a thickness
    grades = bridge_df[bridge_df['thickness_mm'].notna()]
    #totals grades per thickness in ascending order
    counts = grades['thickness_mm'].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(9,6))
    ax.bar(counts.index.astype(str), counts.values, color='steelblue', width=0.6)
    ax.set_xlabel("Sheet thickness (mm)")
    ax.set_ylabel("Number of grades")
    ax.set_title("Grades sheet thickness distribution")

    for i, v in enumerate(counts.values):
        ax.text(i, v, str(v), ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    outpath = DATA_PROCESSED / "thickness_distribution.png"
    plt.savefig(outpath, dpi=120)
    plt.close()
    print(f"Saved thicnkess distribution to: {outpath.name}")

def run_stage7():
    # calls the functions and prints the results for display
    print("\n=== Stage 7: Cost Model (data prep(bridge)) ===")

    input_path = DATA_PROCESSED / "entities_normalised.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Missing {input_path}. please run stage 4 first")

    df = pd.read_csv(input_path)

    #bridge construction
    bridge_df = build_bridge_table(df)
    #plotting bridge construciton
    plot_cost_curve(bridge_df)
    plot_thickness_distribution(bridge_df)

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



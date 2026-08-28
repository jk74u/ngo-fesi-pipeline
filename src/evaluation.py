# src/evaluation.py
import pandas as pd
from src.config import DATA_PROCESSED
from src.s6_time import load_year_map, assign_year_and_bucket, prevalance_over_time

# each evaluation reads a saved pipeline output and presents/computes
# the metric for the Results chapter. Run standalone, not part of the pipeline.
def b1_stage7_precision():
    print("\n--B1: Stage 7 Grade & Thickness Precision--")

    df = pd.read_csv(DATA_PROCESSED / "cost_bridge.csv")

    df_grades = df[df['thickness_mm'].notna()]
    df_unique = df_grades[['entity_text', 'thickness_mm', 'relative_price_eur_kg']].drop_duplicates()
    df_unique = df_unique.sort_values('thickness_mm')

    print(df_unique.to_string(index=False))

    out_path = DATA_PROCESSED / "s7_precision_check.csv"
    df_unique.to_csv(out_path, index=False)

    print(f"\nSaved {len(df_unique)} parsed grades to {out_path.name}")
    print("Action: open file and add Yes or no based on correctness")
    print(f" Precision = correct count / {len(df_unique)}.")

def b2_stage7_sensitivity():
    print("\n--B2: Stage 7 Sensitivity (+/-)--")

    df = pd.read_csv(DATA_PROCESSED / "cost_bridge.csv")
    g = df[df['thickness_mm'].notna()][['entity_text', 'thickness_mm']].drop_duplicates().copy()

    #baseline
    g['price_baseline'] = 0.35 / g['thickness_mm'] 
    #+10% thickness
    g['thick_plus10'] = g['thickness_mm'] * 1.10
    g['price_plus10'] = 0.35 / g['thick_plus10']
    g['pct_change_plus10'] = ((g['price_plus10'] / g['price_baseline']) - 1) * 100
    #10%-
    g['thick_minus10'] = g['thickness_mm'] * 0.90
    g['price_minus10'] = 0.35 / g['thick_minus10']
    g['pct_change_minus10'] = ((g['price_minus10'] / g['price_baseline']) - 1) * 100

    out_path = DATA_PROCESSED / "s7_sensitivity.csv"
    g.to_csv(out_path, index=False)

    print(g[['entity_text', 'thickness_mm', 'price_baseline', 'pct_change_plus10', 'pct_change_minus10']].head(10).to_string(index=False))
    print("... (truncated for terminal)")
    print(f"\nSaved full sensitivity table to {out_path.name}")
    print("Finding: A ±10% thickness error yields a -9.1% / +11.1% price change, uniform across all grades.")
    print("Sensitivity is uniform because the Hemsen model relationship is strictly multiplicative.")
def b3_stage6_unitisation():
    print("\n--B3: Stage 6 unitisation (docs against mentions)")
    df = pd.read_csv(DATA_PROCESSED / "entities_normalised.csv")
    # Competeing material focus
    ents_focus = df[df['label'] == 'COMPETING_MATERIAL']

    year_map = load_year_map()
    ents_bucketed = assign_year_and_bucket(ents_focus, year_map)

    #calculating prevelance both for docs and mentions
    doc_counts = prevalance_over_time(ents_bucketed, 'label', count_mode="docs").T
    mention_counts = prevalance_over_time(ents_bucketed, 'label', count_mode="chunks").T

    # side by side comparision
    comparison = doc_counts.join(mention_counts, lsuffix='_docs', rsuffix='_mentions')

    out_path = DATA_PROCESSED / "s6_unitisation_comparison.csv"
    comparison.to_csv(out_path)
    
    print(comparison.to_string())
    print(f"\nSaved unitisation comparison to {out_path.name}")
    print("Finding: Note how mention-level counting artificially inflates trends in later buckets (e.g., DOE report influence).")

def b4_stage3_precision():
    print("\n--B4: satge 3 precision sampling test--")
    df = pd.read_csv(DATA_PROCESSED / "entities.csv")

    domain_labels = [
        'GRADE', 'CORE_LOSS', 'SI_CONTENT', 'MPA_VALUE', 'FLUX_DENSITY',
        'APPLICATION', 'COMPETING_MATERIAL', 'PRODUCER', 'PROCESSING',
        'GRADE_BRAND', 'STANDARD', 'TEST_METHOD', 'OOS_GRADE'
    ]

    samples = []
    for label in domain_labels:
        subset = df[df['label'] == label]
        if len(subset) == 0:
            continue

        n_sample = min(25, len(subset))
        sampled_subset = subset.sample(n=n_sample, random_state=42) #seeded for reproducibility
        samples.append(sampled_subset)

    stratified_sample = pd.concat(samples)

    cols_to_keep = ['doc_id', 'entity_text', 'label', 'context', 'start_char', 'end_char']
    final_cols = [c for c in cols_to_keep if c in stratified_sample.columns]
    out_df = stratified_sample[final_cols]
    
    out_path = DATA_PROCESSED / "s3_precision_sample.csv"
    out_df.to_csv(out_path, index=False)
    
    print("Sample sizes per label (n per stratum):")
    print(out_df['label'].value_counts().to_string())
    print(f"\nSaved {len(out_df)} total samples to {out_path.name}")
    print("Action: Open this file and score each extraction against your predefined criteria:")
    print("  (a) Label correct? (b) Span boundaries exact? (c) Genuine mention vs. table artifact?")

if __name__ == "__main__":
    b1_stage7_precision()
    b2_stage7_sensitivity()
    b3_stage6_unitisation()
    b4_stage3_precision()




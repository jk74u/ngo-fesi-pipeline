import pandas as pd
import matplotlib.pyplot as plt
from src.config import DATA_PROCESSED, START_YEAR, BUCKET_YEARS

def load_year_map():
    # creates a dictionary mapping bettween doc_id and publication year
    corpus_path = DATA_PROCESSED / "corpus_filtered.csv"
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus file not found at {corpus_path}")
    
    df = pd.read_csv(corpus_path)
    relevant_df = df[df['is_relevant'] == True]

    return dict(zip(relevant_df['doc_id'], relevant_df['year']))

def assign_year_and_bucket(df, year_map):
    # maps the publi year to post cluster dataframe and groups them in 5 year buckets

    #assiging the year from the map
    df['year'] = df['doc_id'].map(year_map)

    #drops the rows where years are missing
    df = df.dropna(subset=['year']).copy()

    #checking the year is a int
    df['year'] = df['year'].astype(int)

    #calculating the start of time period for the bucket
    df['bucket'] = START_YEAR + ((df['year'] - START_YEAR) // BUCKET_YEARS) * BUCKET_YEARS

    #creats a period label 
    df['bucket_label'] = df['bucket'].astype(str) + "-" + (df['bucket'] + BUCKET_YEARS - 1).astype(str)

    return df

def prevalance_over_time(df, category_col, count_mode="docs"):
    # groups the documents into the buckets 
    if count_mode == "docs":
        #counting n.o of docs per bucket
        grouped = df.groupby(['bucket_label', category_col])['doc_id'].nunique()
    elif count_mode == "chunks":
        #counts raw chunks instaed
        grouped = df.groupby(['bucket_label', category_col]).size()
    else:
        raise ValueError("count_mode muct be docs or chunks")
    
    table = grouped.unstack(fill_value=0)

    return table

def plot_trends(table, title, outpath):
    #filterab le line chart 
    #table.T.plot(kind='line', marker='o', figsize=(10,6))
    plot_table = table.T.sort_index()
    plot_table.plot(kind='line', marker='o', figsize=(10, 6))

    plt.title(title)
    plt.xlabel("Period")
    plt.ylabel("Document count")

    #creates the key: or (legend)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7)

    plt.tight_layout()
    plt.savefig(outpath, dpi=120)
    plt.close()

def plot_stacked(table, title, outpath):
    plot_table = table.T.sort_index()
    ax = plot_table.plot(kind= 'bar', stacked=True, figsize=(10, 6))

    for i, bucket in enumerate(plot_table.index):
        total = plot_table.loc[bucket].sum()
        if total ==0:
            continue
        cumulative = 0
        for col in plot_table.columns:
            value = plot_table.loc[bucket, col]
            if value > 0:
                pct = value / total * 100
                # Ensuring onyl big enough segments are annotated
                if pct >=1:
                    ax.text(i, cumulative + value/2, f"{pct:.0f}%", ha ='center', va='center', fontsize=7)
                cumulative += value



    plt.title(title)
    plt.xlabel("Period")
    plt.ylabel("Document count")

    #creates the key: or (legend)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7)

    plt.tight_layout()
    plt.savefig(outpath, dpi=120)
    plt.close()

def run_stage6():
    #plots the trends through the buckets showing prevalance over time
    print("\n=== Starting Stage 6 time period analysis===")

    year_map = load_year_map()
    corpus_df = pd.DataFrame({'doc_id': list(year_map.keys()), 'year': list(year_map.values())})
    corpus_bucketed = assign_year_and_bucket(corpus_df, year_map)
    docs_per_bucket = corpus_bucketed.groupby('bucket_label')['doc_id'].nunique()

    print("\n--- documents per bucket visual---")
    for bucket, count in docs_per_bucket.items():
        print(f" {bucket}: {count} docs")
    print(" these shows the corpus distribution and could change depending on corpus intake")
    print("-" * 50)

    #TOPICS OVER TIME
    units_path = DATA_PROCESSED / "units_clustered.csv"
    if units_path.exists():
        print("\nProcessing Topics over Time...")
        units = pd.read_csv(units_path)
        units = assign_year_and_bucket(units, year_map)

        # Calculate docs per bucket per topic
        topic_trends = prevalance_over_time(units, 'topic', count_mode="docs")
        topic_trends = topic_trends.T

        # mappping the names to topic numbers
        topic_info = pd.read_csv(DATA_PROCESSED / "topic_info.csv")
        topic_name_map = dict(zip(topic_info['Topic'], topic_info['Name']))

        #saving it to a csv file
        topic_csv_path = DATA_PROCESSED / "topic_trends.csv"
        topic_trends.to_csv(topic_csv_path)
        print(f"Saved topic trends to: {topic_csv_path.name}")

        #plotting the relevant topics
        valid_topics = [t for t in topic_trends.index if str(t) != '-1']
        top_topics = topic_trends.loc[valid_topics].sum(axis=1).nlargest(5).index
        plot_trends(
            topic_trends.loc[top_topics].rename(index=topic_name_map),
            " top 5 topics over Time (Distinct Docs)",
            DATA_PROCESSED / "topic_trends_top5.png"
        )
        print("saved topic trends plot to: topic_trends_top5.png")
        #plotting relevant topics
        steel_topics = [0, 5, 15, 17, 38]
        #protection to make sure only indexed topics are plotted here
        active_steel_topics = [t for t in steel_topics if t in topic_trends.index]

        if active_steel_topics:
            plot_trends(
                topic_trends.loc[active_steel_topics].rename(index=topic_name_map),
                "Steel-Relevant Topics Over Time (Distic Docs)",
                DATA_PROCESSED / "topic_trends_steel.png"
            )
            print("E-steel relevant topics saved to : topic_trends_steel.png")
    else:
        print(f"\n WARNING: {units_path.name} not found. skipping topic trends")

    # Entities over time
    ents_path = DATA_PROCESSED / "entities_normalised.csv"
    if ents_path.exists():
        print("\nProcessing Entities over time...")
        ents = pd.read_csv(ents_path)
        ents = assign_year_and_bucket(ents , year_map)

        comp = ents[ents['label'] == 'COMPETING_MATERIAL'] 

        if not comp.empty:
            comp_trends = prevalance_over_time(comp, 'entity_text', count_mode = "docs")
            comp_trends = comp_trends.T

            comp_csv_path = DATA_PROCESSED / "competitor_trends.csv"
            comp_trends.to_csv(comp_csv_path)
            print(f"Saved competitor trends to: {comp_csv_path.name}")

            plot_stacked(
                comp_trends,
                "Competing Material Movement Over TIme",
                DATA_PROCESSED / "competitor_trends_stacked.png"
            )
            print("SAved competitor stacked plot to: competitor_trends_stacked.png")
        else:
            print("No COMPETING_MATERIAL entities found to plot")
        
        apps = ents[ents['label'] == 'APPLICATION'] 

        if not apps.empty:
            app_trends = prevalance_over_time(apps, 'entity_text', count_mode = "docs")
            app_trends = app_trends.T

            app_csv_path = DATA_PROCESSED / "application_trends.csv"
            app_trends.to_csv(app_csv_path)
            print(f"Saved competitor trends to: {app_csv_path.name}")

            top_apps = app_trends.sum(axis=1).nlargest(8).index
            plot_stacked(
                app_trends.loc[top_apps],
                "Application Movement Over TIme",
                DATA_PROCESSED / "application_trends_stacked.png"
            )
            print("SAved applications stacked plot to: application_trends_stacked.png")
        else:
            print("No Application entities found to plot")
    else:
            print(f"\nWARNING: {ents_path.name} not found. Skipping entity trends" )
        

        #focusing on chosing entites that might help describve market movement
        #ents_focus = ents[ents['label'].isin(['COMPETING_MATERIAL', 'APPLICATION'])]

        #if not ents_focus.empty:
            #entity_trends = prevalance_over_time(ents_focus, 'label', count_mode="docs")

            #saving to csv
            #ent_csv_path = DATA_PROCESSED / "entity_trends.csv"
            #entity_trends.to_csv(ent_csv_path)
            #print(f"Saved entity trends to: {ent_csv_path.name}")

            # plot
            #plot_trends(
                #entity_trends,
                #"Market movement over time",
                #DATA_PROCESSED / "entity_trends.png"
           # )
           # print("Saved entity trends plot to: entity_trends.png")
        #else:
           # print("No COMPETING_MATERIAL OR APPLICATION entities found to plot")
   # else:
            #print(f"\nWARNING: {ents_path.name} not found. Skipping entity trends" )
    print("\n=== Stage 6 compelete ===")

if __name__ == "__main__":
    run_stage6()

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from src.config import DATA_PROCESSED, CLUSTER_UNIT, CHUNK_SIZE_CHARS, CHUNK_MIN_CHARS, EMBED_MODEL, RANDOM_SEED
from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
from umap import UMAP



def prepare_units():
    #loads corpus segments into clustering untis ready for bert to ingest
    corpus_path = DATA_PROCESSED / "corpus_filtered.csv"

    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus file could not be found at {corpus_path}")
    
    df = pd.read_csv(corpus_path)
    relevant_df = df[df['is_relevant'] == True]
    
    units = []

    for _, row in relevant_df.iterrows():
        doc_id = row.get('doc_id', 'Unknown')
        text = row['text']

        #Checks that the input is a string
        if not isinstance(text, str):
            continue
        
        #Branch logic that is configurable based on setup
        if CLUSTER_UNIT == 'document':
            units.append({
                "doc_id": doc_id,
                "unit_id": str(doc_id),
                "text": text
            })
        
        elif CLUSTER_UNIT == "chunk":
            #Fixed chunk size
            for start in range(0, len(text), CHUNK_SIZE_CHARS):
                chunk = text[start:  start + CHUNK_SIZE_CHARS]

                #dropping any traling noise through minimum character liimit
                if len(chunk) >= CHUNK_MIN_CHARS:
                    units.append({
                        "doc_id": doc_id,
                        "unit_id": f"{doc_id}_chunk_{start}",
                        "text": chunk
                    })
    return pd.DataFrame(units)


def embed_units(units_df):
    #turns text units into vectors
    print(f"loading SentenceTransformer model '{EMBED_MODEL}' ...")
    model = SentenceTransformer(EMBED_MODEL)

    texts = units_df['text'].tolist()

    print("Encoding texts into vectors...")
    #showing progress bar of them not necessery but cool man
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings

def cluster_units(texts, embeddings):
    print(f"\nConfiguring UMAP with RANDOM_SEED={RANDOM_SEED}...")
    umap_model = UMAP(
        n_neighbors=15,
        n_components=5,
        min_dist=0.0,
        metric= 'cosine',
        random_state=RANDOM_SEED

    )

    print("Initialising BERTopic (min_topic_size=10)...")
    topic_model = BERTopic(
        umap_model=umap_model,
        min_topic_size=10,
        verbose=True
    )

    print("Fitting topic model with pre-computed embeddings...")
    topics, probs = topic_model.fit_transform(texts, embeddings=embeddings)

    return topic_model, topics
def plot_topic_sizes(topic_info):
    # dropping the -1 topic as its not real
    ti = topic_info[topic_info['Topic'] != -1]
    # takes the largest topics by chunk size and put in ascending order
    top = ti.nlargest(12, 'Count').sort_values('Count') 

    fig, ax = plt.subplots(figsize=(10,6))
    #colors relevant topics to non relevant
    steel_topics = [0, 5, 15, 17, 38]
    colors  = ['tab:orange' if t in steel_topics else 'steelblue' for t in top['Topic']]

    ax.barh(top['Name'], top['Count'], color=colors)
    ax.legend(handles=[
    Patch(color='tab:orange', label='Steel-relevant topic'),
    Patch(color='steelblue', label='Other topic')
    ], loc='lower right', fontsize=8)

    ax.set_xlabel("Number of Chunks")
    ax.set_ylabel("Topic")
    ax.set_title("Largest topics by chunk count")

    for i, v in enumerate(top['Count']):
        ax.text(v, i, f" {v}", va='center', fontsize=8)
    
    plt.tight_layout()
    outpath = DATA_PROCESSED / "topic_sizes.png"
    plt.savefig(outpath, dpi=120)
    plt.close()
    print(f"saved topic sizes to: {outpath.name}")

def run_stage5():
    units = prepare_units()
    print(f"{units['doc_id'].nunique()} docs -> {len(units)} units")
    print("\nSample units:")
    print(units[['unit_id', 'text']].head(2).to_string())

    embeddings = embed_units(units)
    print(f"\nEmbedded {len(embeddings)} units, vector dimension: {embeddings.shape[1]}")

    # clustering segment
    texts = units['text'].tolist()
    topic_model, topics = cluster_units(texts, embeddings)
    print("\n===TOPIC-OVERVIEW===")
    print(topic_model.get_topic_info().to_string()) # to.string done so panda prints full table and nothign is truncated
    #Assigning each unit wiht a topic
    units['topic'] = topics
    # attaching the topics keyword as a label
    topic_info = topic_model.get_topic_info()
    topic_names = dict(zip(topic_info['Topic'], topic_info['Name']))
    units['topic_name'] = units['topic'].map(topic_names)
    plot_topic_sizes(topic_info)
    #Saving output
    output_path = DATA_PROCESSED / "units_clustered.csv"
    units.to_csv(output_path, index=False)
    print(f"\nSaved clustered untis to: {output_path}")
    #topic info
    topic_info_path = DATA_PROCESSED / "topic_info.csv"
    topic_info.to_csv(topic_info_path, index=False)
    print(f"Saved topic info to {topic_info_path}")
    


    print("=== STAGE 5 COMPELETE ===")

if __name__ == "__main__":
    run_stage5()

    

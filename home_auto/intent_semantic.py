import pandas as pd
import torch
from sentence_transformers import SentenceTransformer, util

# Load model
model = SentenceTransformer("models/all-MiniLM-L6-v2")

# Load dataset
df = pd.read_csv("dataset4.csv")

# Clean data
df["text"] = df["text"].astype(str).str.lower().str.strip()
df["intent"] = df["intent"].astype(str).str.strip()

# Intent mapping
MAP = {
    "light_off": 0, "0": 0, "0.0": 0,
    "light_on": 1, "1": 1, "1.0": 1,
    "fan_off": 2, "2": 2, "2.0": 2,
    "fan_on": 3, "3": 3, "3.0": 3,
    "pump_off": 4, "4": 4, "4.0": 4,
    "pump_on": 5, "5": 5, "5.0": 5
}

# Convert all intent values to numeric codes
converted_intents = []
clean_texts = []

for t, i in zip(df["text"], df["intent"]):
    key = i.strip().lower()
    if key in MAP:
        clean_texts.append(t)
        converted_intents.append(MAP[key])

# Now we have a clean dataset
dataset_sentences = clean_texts
dataset_intents = converted_intents

print("Loaded", len(dataset_sentences), "valid training samples.")

# Create embeddings for dataset
dataset_embeddings = model.encode(dataset_sentences, convert_to_tensor=True)


def detect_intents(user_text, threshold=0.45):

    if len(dataset_embeddings) == 0:
        return "null"

    text = user_text.lower().strip()
    input_emb = model.encode(text, convert_to_tensor=True)

    scores = util.cos_sim(input_emb, dataset_embeddings)[0]

    top_k = 10
    top_results = torch.topk(scores, k=top_k)

    detected = {}

    for idx, score in zip(top_results.indices, top_results.values):
        code = dataset_intents[int(idx)]

        if float(score) < threshold:
            continue

        # Determine device category
        if code in [0, 1]:
            device = "light"
        elif code in [2, 3]:
            device = "fan"
        else:
            device = "pump"

        # Keep only highest score per device
        if device not in detected or float(score) > detected[device][1]:
            detected[device] = (code, float(score))

    if len(detected) == 0:
        return "null"

    # sort by device order
    order = {"light": 1, "fan": 2, "pump": 3}

    final = ""
    for dev in sorted(detected.keys(), key=lambda x: order[x]):
        final += str(detected[dev][0])

    return final

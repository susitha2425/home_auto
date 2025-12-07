import pandas as pd
import string
import joblib
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score

def clean_text(text):
    if pd.isna(text):
        return ""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text.strip()

def load_and_prepare_data(filename):
    df = pd.read_csv(filename)
    df.columns = df.columns.str.strip().str.lower()

    if 'text' not in df.columns or 'intent' not in df.columns:
        raise ValueError("'text' and 'intent' columns are required.")

    df.dropna(subset=["text", "intent"], inplace=True)
    df["text"] = df["text"].apply(clean_text)
    df["intent"] = df["intent"].astype(str).str.strip()

    df = df[df["text"] != ""]
    df = df[df["intent"] != ""]
    return df

def train_model(df):
    X = df["text"]
    y = df["intent"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
        ("clf", RandomForestClassifier(n_estimators=500, random_state=42))
    ])

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Model trained successfully | Accuracy: {acc * 100:.2f}%")

    joblib.dump(pipeline, "intent_model.pkl")
    return pipeline

def load_model():
    if not os.path.exists("intent_model.pkl"):
        raise FileNotFoundError(" Trained model not found.")
    return joblib.load("intent_model.pkl")

def predict_intent(model, command):
    cleaned = clean_text(command)
    return model.predict([cleaned])[0]  

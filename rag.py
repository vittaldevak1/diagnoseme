import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# Load datasets
desc_df = pd.read_csv("symptom_Description.csv")
prec_df = pd.read_csv("symptom_precaution.csv")
symp_df = pd.read_csv("dataset.csv")

# Build documents
documents = []

for _, row in desc_df.iterrows():
    disease = row["Disease"]
    description = row["Description"]

    # Get precautions
    precautions_row = prec_df[prec_df["Disease"] == disease]
    precautions = []
    if not precautions_row.empty:
        precautions = precautions_row.iloc[0].drop("Disease").dropna().tolist()

    # Get symptoms
    symp_rows = symp_df[symp_df["Disease"] == disease]
    symptoms = []
    if not symp_rows.empty:
        symptoms = symp_rows.iloc[0].drop("Disease").dropna().tolist()

    doc = f"""
Disease: {disease}
Symptoms: {", ".join(symptoms)}
Description: {description}
Precautions: {", ".join(precautions)}
"""
    documents.append(doc)

# Create TF-IDF vectors
vectorizer = TfidfVectorizer()
doc_vectors = vectorizer.fit_transform(documents)

# Retrieval function
def retrieve_context(user_input, top_k=3):
    query_vec = vectorizer.transform([user_input])

    scores = (doc_vectors @ query_vec.T).toarray().flatten()
    top_indices = np.argsort(scores)[-top_k:]

    return [documents[i] for i in top_indices]

import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder
import joblib

# === Step 1: Load the dataset ===
data_path = "ml/dummy_expenses.csv"
df = pd.read_csv(data_path)

# Drop any rows with missing data just in case
df.dropna(subset=["note", "category"], inplace=True)

X = df["note"]
y = df["category"]

# === Step 2: Encode category labels ===
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# === Step 3: Train/test split ===
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42
)

# === Step 4: TF-IDF vectorization ===
vectorizer = TfidfVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# === Step 5: Train the model ===
model = MultinomialNB()
model.fit(X_train_vec, y_train)

# === Step 6: Evaluation ===
y_pred = model.predict(X_test_vec)
print(f"\nAccuracy: {accuracy_score(y_test, y_pred):.2f}")
print("\nClassification Report:\n", classification_report(
    y_test, y_pred, target_names=label_encoder.classes_)
)

# === Step 7: Save trained model and transformers ===
os.makedirs("ml/models", exist_ok=True)

joblib.dump(model, "ml/models/expense_category_model.pkl")
joblib.dump(vectorizer, "ml/models/tfidf_vectorizer.pkl")
joblib.dump(label_encoder, "ml/models/category_label_encoder.pkl")

print("\n✔ Model and vectorizer saved to ml/models/")

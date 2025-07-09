import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# Load all user data
df = pd.read_csv("ml/dummy_expenses.csv")

X = df['note']
y = df['category']

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

X_train, _, y_train, _ = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

vectorizer = TfidfVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)

model = MultinomialNB()
model.fit(X_train_vec, y_train)

# Save updated model
os.makedirs("ml/models", exist_ok=True)
joblib.dump(model, "ml/models/expense_category_model.pkl")
joblib.dump(vectorizer, "ml/models/tfidf_vectorizer.pkl")
joblib.dump(label_encoder, "ml/models/category_label_encoder.pkl")

print("✅ Model retrained and saved.")

import joblib
import re
import nltk
from nltk.corpus import stopwords

# Download NLTK stopwords if not already present
nltk.download('stopwords', quiet=True)
stop_words = set(stopwords.words('english'))

# Load trained model and transformers
model = joblib.load("ml/models/expense_category_model.pkl")
vectorizer = joblib.load("ml/models/tfidf_vectorizer.pkl")
label_encoder = joblib.load("ml/models/category_label_encoder.pkl")

def clean_text(text):
    """
    Preprocess the input note by:
    - Lowercasing
    - Removing non-alphabetic characters
    - Removing stopwords
    """
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)  # Remove punctuation and digits
    tokens = text.split()
    tokens = [word for word in tokens if word not in stop_words]
    return " ".join(tokens)

def predict_category(note):
    """
    Predicts category for the given note using trained ML model.
    """
    cleaned_note = clean_text(note)
    note_vector = vectorizer.transform([cleaned_note])
    predicted_encoded_label = model.predict(note_vector)[0]
    predicted_category = label_encoder.inverse_transform([predicted_encoded_label])[0]
    return predicted_category


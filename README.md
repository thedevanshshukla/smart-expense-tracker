# 💰 Smart Expense Tracker

A powerful, AI-enhanced web application to help you track, manage, and visualize your expenses. This app automatically predicts the category of your expense using a machine learning model and provides features like exporting, filtering, and analytics.

---

## 🚀 Features

- 🔐 User Authentication (Login/Logout)
- 📝 Add New Expenses with Notes, Amount, Date
- 🤖 Auto-Categorization using Machine Learning (with manual override)
- 📊 View Daily and Monthly Visual Graphs
- 🔍 Filter by Category, Date Range, Month, or Year
- 📥 Export Filtered Expenses to CSV and PDF
- 🗑️ Delete Expense with Confirmation Modal
- 🎨 Clean and Responsive UI with Carousel Pagination

---

## 🧱 Tech Stack

### Backend
- Python 3.x
- Flask
- Flask-SQLAlchemy (ORM)
- WTForms (Form Validation)

### Machine Learning
- Scikit-learn
- TF-IDF Vectorizer (for text features)
- Naive Bayes Classifier (for category prediction)
- Label Encoder (for label transformation)
- joblib (model serialization)

### Frontend
- HTML5, CSS3
- Bootstrap 5
- Jinja2 (Template Engine)
- JavaScript (for pagination)

### Data Visualization
- Chart.js

### Export Tools
- CSV (Python csv module)
- PDF (xhtml2pdf / pisa)

---


## 🔁 Workflow

1. User logs in.
2. On dashboard, user adds an expense.
3. ML model predicts category (user can override).
4. Expense is saved to database.
5. User filters, exports, or views charts.

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/thedevanshshukla/smart-expense-tracker.git
cd smart-expense-tracker

# Create and activate a virtual environment
python -m venv expenseTracker
# On Windows:
expenseTracker\Scripts\activate
# On Unix/Mac:
source expenseTracker/bin/activate

# Install dependencies
pip install -r requirements.txt

# Train the ML model
python ml/train.py

# Run the application
flask run
```

---

## 🌱 Future Enhancements

- Chat-based AI assistant for spending suggestions
- Advanced category prediction using deep learning
- Goal-setting and budget tracking
- Cloud deployment (e.g., Heroku, Render)

---

## 👤 Author

**Devansh Shukla**  
*Smart Expense Tracker Project - 2025*

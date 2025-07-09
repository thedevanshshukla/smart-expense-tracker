from flask import render_template, redirect, url_for, flash, session, request, Blueprint, make_response
from .forms import ExpenseForm
from models import db, Expense
from datetime import datetime, timedelta
import csv
import io
from xhtml2pdf import pisa
from flask import jsonify
from sqlalchemy import func
from ml.predict import predict_category
import csv


dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# --- Predict Category ---


# --- Shared Filter Logic ---
def get_filtered_expenses(filters):
    user_id = session.get("user_id")
    if not user_id:
        return []

    query = Expense.query.filter_by(user_id=user_id)

    category_filter = filters.get('category', '').strip().lower()
    time_filter = filters.get('time_filter', '').lower()
    selected_year = int(filters.get('year')) if filters.get('year') else None
    selected_month = int(filters.get('month')) if filters.get('month') else None
    start_date = filters.get('start_date')
    end_date = filters.get('end_date')

    if category_filter:
        query = query.filter(db.func.lower(Expense.category) == category_filter)

    if start_date or end_date:
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Expense.created_at >= start)
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Expense.created_at < end)
    elif selected_year or selected_month:
        if selected_year and selected_month:
            start = datetime(selected_year, selected_month, 1)
            end = datetime(selected_year + int(selected_month == 12), (selected_month % 12) + 1, 1)
        elif selected_year:
            start = datetime(selected_year, 1, 1)
            end = datetime(selected_year + 1, 1, 1)
        else:
            start = end = None

        if start and end:
            query = query.filter(Expense.created_at >= start, Expense.created_at < end)
    elif time_filter:
        now = datetime.now()
        if time_filter == 'week':
            start = now - timedelta(days=now.weekday())
        elif time_filter == 'month':
            start = now.replace(day=1)
        elif time_filter == 'year':
            start = now.replace(month=1, day=1)
        else:
            start = None
        if start:
            query = query.filter(Expense.created_at >= start)

    return query.order_by(Expense.created_at.desc()).all()

@dashboard_bp.route("/predict-category", methods=["POST"])
def predict_category_route():
    from ml.predict import predict_category  # ensure correct path
    data = request.get_json()
    note = data.get("note", "")
    if not note:
        return jsonify({"error": "Note is required"}), 400

    category = predict_category(note)
    return jsonify({"category": category})

# --- Dashboard Route ---
@dashboard_bp.route('/', methods=['GET', 'POST'])
def dashboard_home():
    if 'user_id' not in session:
        flash('Login required.', 'warning')
        return redirect(url_for('auth.login'))

    form = ExpenseForm()
    user_id = session['user_id']

    if form.validate_on_submit():
        category = form.category.data.strip() or predict_category(form.note.data)
        selected_date = form.date.data or datetime.now().date()
        selected_datetime = datetime.combine(selected_date, datetime.now().time())
        with open("ml/dummy_expenses.csv", "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([form.note.data.strip(), category])
        new_expense = Expense(
            user_id=user_id,
            amount=form.amount.data,
            title=form.note.data,
            category=category,
            created_at=selected_datetime
        )
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('dashboard.dashboard_home'))

    filters = request.args.to_dict()
    filtered_expenses = get_filtered_expenses(filters)
    total_filtered_spent = sum(exp.amount for exp in filtered_expenses)

    all_expenses = Expense.query.filter_by(user_id=user_id).all()
    total_spent = sum(exp.amount for exp in all_expenses)

    raw_categories = db.session.query(Expense.category).filter_by(user_id=user_id).distinct().all()
    categories = sorted(set(cat[0].title() for cat in raw_categories))

    return render_template(
        'dashboard/dashboard.html',
        form=form,
        expenses=filtered_expenses,
        user_name=session.get('user_name'),
        current_date=datetime.now().strftime('%Y-%m-%d'),
        categories=categories,
        selected_category=filters.get("category", ""),
        time_filter=filters.get("time_filter", ""),
        selected_year=filters.get("year"),
        selected_month=str(filters.get("month")).zfill(2) if filters.get("month") else "",
        selected_start=filters.get("start_date", ""),
        selected_end=filters.get("end_date", ""),
        total_spent=total_spent,
        total_filtered_spent=total_filtered_spent
    )

# --- Delete Route ---
@dashboard_bp.route('/delete/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    if 'user_id' not in session:
        flash("Login required.", "warning")
        return redirect(url_for('auth.login'))

    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != session['user_id']:
        flash("Unauthorized deletion attempt.", "danger")
        return redirect(url_for('dashboard.dashboard_home'))

    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted successfully.", "success")
    return redirect(url_for('dashboard.dashboard_home'))

# --- Export CSV ---
@dashboard_bp.route('/export/csv')
def export_csv():
    filters = request.args.to_dict()
    expenses = get_filtered_expenses(filters)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Amount', 'Category', 'Note'])
    for exp in expenses:
        writer.writerow([
            exp.created_at.strftime("%d-%b-%Y"),
            f"{exp.amount:.2f}",
            exp.category,
            exp.title
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=expenses.csv"
    response.headers["Content-type"] = "text/csv"
    return response

# --- Export PDF ---
@dashboard_bp.route('/export/pdf')
def export_pdf():
    filters = request.args.to_dict()
    expenses = get_filtered_expenses(filters)

    rendered = render_template("pdf_template.html", expenses=expenses)
    pdf = io.BytesIO()
    pisa.CreatePDF(io.StringIO(rendered), dest=pdf)

    response = make_response(pdf.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=expenses.pdf"
    response.headers["Content-type"] = "application/pdf"
    return response
# --- Expense Visualization Page ---
@dashboard_bp.route('/visualize')
def visualize_page():
    if 'user_id' not in session:
        flash("Login required.", "warning")
        return redirect(url_for('auth.login'))
    return render_template("dashboard/visualize.html")


# --- Chart Data: Category-Wise Daily or Monthly Grouping ---
@dashboard_bp.route('/chart-data/category')
def category_chart_data():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    view = request.args.get("view", "monthly")
    raw_query = db.session.query(
        func.date(Expense.created_at) if view == 'daily' else func.strftime('%Y-%m', Expense.created_at),
        Expense.category,
        func.sum(Expense.amount)
    ).filter_by(user_id=user_id).group_by(
        func.date(Expense.created_at) if view == 'daily' else func.strftime('%Y-%m', Expense.created_at),
        Expense.category
    ).all()

    label_key = lambda r: r[0].strftime('%d %b') if view == 'daily' else datetime.strptime(r[0], '%Y-%m').strftime('%b %Y')
    labels = sorted(set(label_key(row) for row in raw_query))
    formatted = [
        {"label": label_key(row), "category": row[1], "amount": float(row[2])}
        for row in raw_query
    ]

    return jsonify({"labels": labels, "data": formatted})






































# from flask import render_template, redirect, url_for, flash, session, request, Blueprint, make_response
# from .forms import ExpenseForm
# from models import db, Expense
# from datetime import datetime, timedelta
# import csv
# import io
# from xhtml2pdf import pisa
# from flask import jsonify
# from sqlalchemy import func

# dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# # --- Predict Category ---
# def predict_category(note):
#     if 'food' in note.lower():
#         return 'Food'
#     elif 'travel' in note.lower():
#         return 'Travel'
#     return 'Other'

# # --- Shared Filter Logic ---
# def get_filtered_expenses(filters):
#     user_id = session.get("user_id")
#     if not user_id:
#         return []

#     query = Expense.query.filter_by(user_id=user_id)

#     category_filter = filters.get('category', '').strip().lower()
#     time_filter = filters.get('time_filter', '').lower()
#     selected_year = int(filters.get('year')) if filters.get('year') else None
#     selected_month = int(filters.get('month')) if filters.get('month') else None
#     start_date = filters.get('start_date')
#     end_date = filters.get('end_date')

#     if category_filter:
#         query = query.filter(db.func.lower(Expense.category) == category_filter)

#     if start_date or end_date:
#         if start_date:
#             start = datetime.strptime(start_date, "%Y-%m-%d")
#             query = query.filter(Expense.created_at >= start)
#         if end_date:
#             end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
#             query = query.filter(Expense.created_at < end)
#     elif selected_year or selected_month:
#         if selected_year and selected_month:
#             start = datetime(selected_year, selected_month, 1)
#             end = datetime(selected_year + int(selected_month == 12), (selected_month % 12) + 1, 1)
#         elif selected_year:
#             start = datetime(selected_year, 1, 1)
#             end = datetime(selected_year + 1, 1, 1)
#         else:
#             start = end = None

#         if start and end:
#             query = query.filter(Expense.created_at >= start, Expense.created_at < end)
#     elif time_filter:
#         now = datetime.now()
#         if time_filter == 'week':
#             start = now - timedelta(days=now.weekday())
#         elif time_filter == 'month':
#             start = now.replace(day=1)
#         elif time_filter == 'year':
#             start = now.replace(month=1, day=1)
#         else:
#             start = None
#         if start:
#             query = query.filter(Expense.created_at >= start)

#     return query.order_by(Expense.created_at.desc()).all()


# # --- Dashboard Route ---
# @dashboard_bp.route('/', methods=['GET', 'POST'])
# def dashboard_home():
#     if 'user_id' not in session:
#         flash('Login required.', 'warning')
#         return redirect(url_for('auth.login'))

#     form = ExpenseForm()
#     user_id = session['user_id']

#     if form.validate_on_submit():
#         category = form.category.data.strip() or predict_category(form.note.data)
#         selected_date = form.date.data or datetime.now().date()
#         selected_datetime = datetime.combine(selected_date, datetime.now().time())
#         new_expense = Expense(
#             user_id=user_id,
#             amount=form.amount.data,
#             title=form.note.data,
#             category=category,
#             created_at=selected_datetime
#         )
#         db.session.add(new_expense)
#         db.session.commit()
#         flash('Expense added successfully!', 'success')
#         return redirect(url_for('dashboard.dashboard_home'))

#     filters = request.args.to_dict()
#     filtered_expenses = get_filtered_expenses(filters)
#     total_filtered_spent = sum(exp.amount for exp in filtered_expenses)

#     all_expenses = Expense.query.filter_by(user_id=user_id).all()
#     total_spent = sum(exp.amount for exp in all_expenses)

#     raw_categories = db.session.query(Expense.category).filter_by(user_id=user_id).distinct().all()
#     categories = sorted(set(cat[0].title() for cat in raw_categories))

#     return render_template(
#         'dashboard/dashboard.html',
#         form=form,
#         expenses=filtered_expenses,
#         user_name=session.get('user_name'),
#         current_date=datetime.now().strftime('%Y-%m-%d'),
#         categories=categories,
#         selected_category=filters.get("category", ""),
#         time_filter=filters.get("time_filter", ""),
#         selected_year=filters.get("year"),
#         selected_month=str(filters.get("month")).zfill(2) if filters.get("month") else "",
#         selected_start=filters.get("start_date", ""),
#         selected_end=filters.get("end_date", ""),
#         total_spent=total_spent,
#         total_filtered_spent=total_filtered_spent
#     )

# # --- Delete Route ---
# @dashboard_bp.route('/delete/<int:expense_id>', methods=['POST'])
# def delete_expense(expense_id):
#     if 'user_id' not in session:
#         flash("Login required.", "warning")
#         return redirect(url_for('auth.login'))

#     expense = Expense.query.get_or_404(expense_id)
#     if expense.user_id != session['user_id']:
#         flash("Unauthorized deletion attempt.", "danger")
#         return redirect(url_for('dashboard.dashboard_home'))

#     db.session.delete(expense)
#     db.session.commit()
#     flash("Expense deleted successfully.", "success")
#     return redirect(url_for('dashboard.dashboard_home'))

# # --- Export CSV ---
# @dashboard_bp.route('/export/csv')
# def export_csv():
#     filters = request.args.to_dict()
#     expenses = get_filtered_expenses(filters)

#     output = io.StringIO()
#     writer = csv.writer(output)
#     writer.writerow(['Date', 'Amount', 'Category', 'Note'])
#     for exp in expenses:
#         writer.writerow([
#             exp.created_at.strftime("%d-%b-%Y"),
#             f"{exp.amount:.2f}",
#             exp.category,
#             exp.title
#         ])

#     response = make_response(output.getvalue())
#     response.headers["Content-Disposition"] = "attachment; filename=expenses.csv"
#     response.headers["Content-type"] = "text/csv"
#     return response

# # --- Export PDF ---
# @dashboard_bp.route('/export/pdf')
# def export_pdf():
#     filters = request.args.to_dict()
#     expenses = get_filtered_expenses(filters)

#     rendered = render_template("pdf_template.html", expenses=expenses)
#     pdf = io.BytesIO()
#     pisa.CreatePDF(io.StringIO(rendered), dest=pdf)

#     response = make_response(pdf.getvalue())
#     response.headers["Content-Disposition"] = "attachment; filename=expenses.pdf"
#     response.headers["Content-type"] = "application/pdf"
#     return response
# # --- Expense Visualization Page ---
# @dashboard_bp.route('/visualize')
# def visualize_page():
#     if 'user_id' not in session:
#         flash("Login required.", "warning")
#         return redirect(url_for('auth.login'))
#     return render_template("dashboard/visualize.html")


# # --- Chart Data: Category-Wise Daily or Monthly Grouping ---
# @dashboard_bp.route('/chart-data/category')
# def category_chart_data():
#     user_id = session.get("user_id")
#     if not user_id:
#         return jsonify({"error": "Unauthorized"}), 401

#     view = request.args.get("view", "monthly")
#     raw_query = db.session.query(
#         func.date(Expense.created_at) if view == 'daily' else func.strftime('%Y-%m', Expense.created_at),
#         Expense.category,
#         func.sum(Expense.amount)
#     ).filter_by(user_id=user_id).group_by(
#         func.date(Expense.created_at) if view == 'daily' else func.strftime('%Y-%m', Expense.created_at),
#         Expense.category
#     ).all()

#     label_key = lambda r: r[0].strftime('%d %b') if view == 'daily' else datetime.strptime(r[0], '%Y-%m').strftime('%b %Y')
#     labels = sorted(set(label_key(row) for row in raw_query))
#     formatted = [
#         {"label": label_key(row), "category": row[1], "amount": float(row[2])}
#         for row in raw_query
#     ]

#     return jsonify({"labels": labels, "data": formatted})


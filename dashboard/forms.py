from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange
from wtforms.fields import DateField


class ExpenseForm(FlaskForm):
    amount = DecimalField('Amount (₹)', validators=[DataRequired(), NumberRange(min=0.01)])
    note = StringField('Note', validators=[DataRequired()])
    category = StringField('Category')  # prefilled using ML
    date = DateField('Date', format='%Y-%m-%d')
    submit = SubmitField('Add Expense')

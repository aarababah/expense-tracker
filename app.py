from os import environ
from flask import Flask, render_template, request, render_template, send_from_directory, jsonify, json, redirect
from sqlalchemy import create_engine, distinct, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from calendar import calendar

# Import modules to declare columns and column data types
from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.orm import Session
from collections import Counter

# Initializing Application
Base = declarative_base()
app = Flask(__name__)
# print(environ.get("APP_ENV"))

#Set Database connection values
HOSTNAME = environ.get("DB_HOSTNAME")
PORT = environ.get("DB_PORT")
USERNAME = environ.get("DB_USERNAME")
PASSWORD = environ.get("DB_PASSWORD")
DIALECT = environ.get("DB_DIALECT")
DRIVER = environ.get("DB_DRIVER")
DATABASE = environ.get("DB_DATABASE")


class MixIn():
    def __repr__(self):
        return f"{self.__tablename__}(transaction_date: {self.transaction_date}, expense_amt: {self.expense_amt}, category: {self.category}, sub_category: {self.sub_category}, payment_method: {self.payment_method}, description: {self.description}, new_category: {self.new_category}, subcategory: {self.subcategory})"
    def to_dict(self):
        return {"expense_id": self.expense_id, "transaction_date": {self.transaction_date}, "expense_amt": self.expense_amt, "category": self.category, "sub_category": self.sub_category, "payment_method": self.payment_method, "description": self.description, "new_category": {self.new_category}, "subcategory": {self.subcategory}}


class ExpenseInfo(Base, MixIn):
    __tablename__ = "expenses"
    expense_id = Column(Integer, primary_key=True)
    transaction_date = Column(Date)
    expense_amt = Column(Integer)
    category = Column(String(40))
    sub_category = Column(String(40))
    payment_method = Column(String(40))
    description = Column(String(500))

class IncomeInfo(Base):
    __tablename__ = "income"
    income_id = Column(Integer, primary_key=True)
    income_date = Column(Date, server_default=func.now())
    income_amt = Column(Integer)

class CategoryInfo(Base, MixIn):
    __tablename__ = "categories"
    new_category = Column(String(25), primary_key=True)
    subcategory = Column(String(25))

# # Establish Connection to a sqlite database
connection_string = (
    f"{DIALECT}+{DRIVER}://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}"
)

print(connection_string)
engine = create_engine(connection_string)
conn = engine.connect()
Base.metadata.create_all(engine)
session = Session(bind=engine)

@app.route('/')
def index():
    return send_from_directory("", "index.html")
    

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    # Get distinct years from the database
    dates_query = session.query(ExpenseInfo.transaction_date.distinct().label("date"))
    dates = [row.date.year for row in dates_query.all()]

    # Get categories from the database
    cat_query = session.query(ExpenseInfo.category.distinct().label("category"))
    categories = [row.category for row in cat_query.all()]

    transactions = session.query(ExpenseInfo)
    credit_amt = session.query(func.sum(ExpenseInfo.expense_amt)).\
                                filter(ExpenseInfo.payment_method == "Credit Card")
    cash_amt = session.query(func.sum(ExpenseInfo.expense_amt)).\
                                filter(ExpenseInfo.payment_method == "Cash")

    income = round(session.query(func.avg(IncomeInfo.income_amt)).scalar(), 0)
   
    expenses = session.query(func.sum(ExpenseInfo.expense_amt))
    
    if income == 0:
        savings_rate = 0
    else:
        savings_rate = round((income - expenses.scalar()) / income * 100, 2)

    return render_template("dashboard.html", 
                            years = Counter(dates).keys(), 
                            categories = Counter(categories).keys(),
                            transactions = transactions.count(),
                            credit_amt = credit_amt.scalar(),
                            cash_amt = cash_amt.scalar(),
                            expenses = expenses.scalar(),
                            income = income,
                            savings_rate = savings_rate)



@app.route("/filters", methods=['GET', 'POST'])
def filters():
    exp_key = []
    exp_val = []
    subcat_key = []
    subcat_val = []

    session.rollback()
    transactions = session.query(ExpenseInfo)
    credit_amt = session.query(func.sum(ExpenseInfo.expense_amt)).\
                                filter(ExpenseInfo.payment_method == "Credit Card")
    cash_amt = session.query(func.sum(ExpenseInfo.expense_amt)).\
                                filter(ExpenseInfo.payment_method == "Cash")

    income = session.query(func.avg(IncomeInfo.income_amt)).scalar()
   
    expenses = session.query(func.sum(ExpenseInfo.expense_amt))

    filters = request.json["filters"]

    if "years" in filters and len(filters["years"])>0:
        years = filters["years"]
        transactions = transactions.filter(func.year(ExpenseInfo.transaction_date).in_(years))
        credit_amt = credit_amt.filter(func.year(ExpenseInfo.transaction_date).in_(years))
        cash_amt = cash_amt.filter(func.year(ExpenseInfo.transaction_date).in_(years))
        expenses = expenses.filter(func.year(ExpenseInfo.transaction_date).in_(years))
        income = session.query(func.avg(IncomeInfo.income_amt)).filter(func.year(IncomeInfo.income_date).in_(years)).order_by(IncomeInfo.income_date.desc()).first()[0]

        # Get expenses when a year selected
        i_expenses = {}
        exp_key = []
        exp_val = []
        expensesTracker = session.query(func.round(func.sum(ExpenseInfo.expense_amt)), 
                            func.month(ExpenseInfo.transaction_date),
                            func.max(ExpenseInfo.transaction_date.cast(Date))).\
                                filter(func.year(ExpenseInfo.transaction_date).in_(years)).\
                            group_by(func.year(ExpenseInfo.transaction_date),
                                    func.month(ExpenseInfo.transaction_date)).\
                            order_by(func.max(ExpenseInfo.transaction_date.cast(Date)))
    
        for e in expensesTracker.all():
             exp_key.append(e[2].strftime("%b"))
             exp_val.append(str(e[0]))


    
    if "months" in filters and len(filters["months"])>0:
        months = filters["months"]
        transactions = transactions.filter(func.month(ExpenseInfo.transaction_date).in_(months))
        credit_amt = credit_amt.filter(func.month(ExpenseInfo.transaction_date).in_(months))
        cash_amt = cash_amt.filter(func.month(ExpenseInfo.transaction_date).in_(months))
        expenses = expenses.filter(func.month(ExpenseInfo.transaction_date).in_(months))
        income = income/12


        # Get expenses by category in a given month
        i_expenses = {}
        exp_key = []
        exp_val = []
        expensesTracker = session.query(func.round(func.sum(ExpenseInfo.expense_amt)), 
                            func.month(ExpenseInfo.transaction_date),
                            ExpenseInfo.category,
                            func.max(ExpenseInfo.transaction_date.cast(Date))).\
                                filter(func.year(ExpenseInfo.transaction_date).in_(years),
                                func.month(ExpenseInfo.transaction_date).in_(months)).\
                            group_by(ExpenseInfo.category)
    
        for e in expensesTracker.all():
             exp_key.append(str(e[2]))
             exp_val.append(str(e[0]))


     
    if "categories" in filters and len(filters["categories"])>0:
        categories = filters["categories"]
        transactions = transactions.filter(ExpenseInfo.category.in_(categories))
        credit_amt = credit_amt.filter(ExpenseInfo.category.in_(categories))
        cash_amt = cash_amt.filter(ExpenseInfo.category.in_(categories))
        expenses = expenses.filter(ExpenseInfo.category.in_(categories))     


        # Get expenses by sub category in a given month
        subcat_key = []
        subcat_val = []
        subcatTracker = session.query(func.round(func.sum(ExpenseInfo.expense_amt)), 
                            func.month(ExpenseInfo.transaction_date),
                            ExpenseInfo.category,
                            ExpenseInfo.sub_category,
                            func.max(ExpenseInfo.transaction_date.cast(Date))).\
                                filter(func.year(ExpenseInfo.transaction_date).in_(years),
                                func.month(ExpenseInfo.transaction_date).in_(months),
                                ExpenseInfo.category.in_(categories)).\
                            group_by(ExpenseInfo.sub_category)
    
        for e in subcatTracker.all():
             subcat_key.append(str(e[3]))
             subcat_val.append(str(e[0]))


    if not credit_amt.scalar():
        credit_amt = 0
    else:
        credit_amt = credit_amt.scalar()

    if not cash_amt.scalar():
        cash_amt = 0
    else:
        cash_amt = cash_amt.scalar()

    if not expenses.scalar():
        expenses = 0
    else:
        expenses = expenses.scalar()

    if income == 0:
        savings_rate = 0
    else:
        savings_rate = round((income - expenses) / income * 100, 2)

    data = {
        "transactions": transactions.count(),
        "credit_amt": str(credit_amt),
        "cash_amt": str(cash_amt),
        "expenses": str(expenses),
        "income": str(round(income, 0)),
        "savings_rate": str(savings_rate),
        "exp_key": exp_key,
        "exp_val": exp_val,
        "subcat_key": subcat_key,
        "subcat_val": subcat_val
    }

    print(data)
    return jsonify(data)


@app.route("/ieplot/<period>", methods=['GET','POST'])
def ieplot(period):
    inc_key = []
    inc_val = []
    exp_key = []
    exp_val = []

    if period == "annual":
        income = session.query(func.round(func.avg(IncomeInfo.income_amt)), 
                        func.year(IncomeInfo.income_date),
                        func.max(IncomeInfo.income_date.cast(Date))).\
                        group_by(func.year(IncomeInfo.income_date))

        expenses = session.query(func.round(func.sum(ExpenseInfo.expense_amt)), 
                        func.year(ExpenseInfo.transaction_date),
                        func.max(ExpenseInfo.transaction_date.cast(Date))).\
                        group_by(func.year(ExpenseInfo.transaction_date))

        for i in income.all():
            inc_key.append(str(i[2].year))
            inc_val.append(str(i[0]))

        for e in expenses.all():
             exp_key.append(str(e[2].year))
             exp_val.append(str(e[0]))




    if period == "monthly":
        income = session.query(func.round(func.avg(IncomeInfo.income_amt)), 
                        func.year(IncomeInfo.income_date),
                        func.month(IncomeInfo.income_date),
                        func.max(IncomeInfo.income_date.cast(Date))).\
                        group_by(func.year(IncomeInfo.income_date),
                                func.month(IncomeInfo.income_date)).\
                        order_by(func.max(IncomeInfo.income_date.cast(Date)))

        expenses = session.query(func.round(func.sum(ExpenseInfo.expense_amt)), 
                        func.year(ExpenseInfo.transaction_date),
                        func.month(ExpenseInfo.transaction_date),
                        func.max(ExpenseInfo.transaction_date.cast(Date))).\
                        group_by(func.year(ExpenseInfo.transaction_date),
                                func.month(ExpenseInfo.transaction_date)).\
                        order_by(func.max(ExpenseInfo.transaction_date.cast(Date)))

        for i in income.all():
            inc_key.append(str(i[3]))
            inc_val.append(str(i[0]/12))

        for e in expenses.all():
             exp_key.append(str(e[3]))
             exp_val.append(str(e[0]))

    data = {
        "inc_key": inc_key,
        "inc_val": inc_val,
        "exp_key": exp_key,
        "exp_val": exp_val
    }

    return jsonify(data)



@app.route("/transactions", methods=['GET','POST'])
def transactions():
    cur = session.execute("select DISTINCT new_category FROM categories")
    data = cur.fetchall()

    cur2 = session.execute("SELECT subcategory FROM categories")
    data2 = cur2.fetchall()

    return render_template("transactions.html", data=data, data2=data2)

@app.route('/home', methods = ['POST'])
def home():
    if request.method == 'POST':
        return render_template('index.html')


@app.route('/submit', methods=['GET','POST'])
def submit():
    if request.method == 'POST':
        transaction_date = request.form['transaction_date']
        expense_amt = request.form['expense_amt']
        category = request.form['category']
        sub_category = request.form['sub_category']
        payment_method = request.form['payment_method']
        description = request.form['description']
        expense_input = ExpenseInfo(transaction_date = transaction_date, 
            expense_amt = expense_amt, category = category, sub_category = sub_category, 
            payment_method = payment_method, description = description)
        session.add(expense_input)
        session.commit()
        
        if transaction_date == "" :
            return render_template('/transactions.html', message = 'Please enter required fields')
        
        return render_template('/transactions.html', message = 'Expense added')


@app.route('/submitincome', methods=['POST'])
def submitincome():
    session.rollback()
    if request.method == 'POST':
        incomeamt = request.json["incomeamt"]

        if incomeamt == "" :
            message = "A value is required"
        else:
            income_input = IncomeInfo(income_amt = incomeamt)
            session.add(income_input)
            session.commit()
            message = "Income added"
            
        data = {
             "message": message
        }
            
        return jsonify(data)


@app.route('/addcat', methods=['POST'])
def addcat():
     if request.method == 'POST':
        new_category = request.form['new_category']
        subcategory = request.form['subcategory']
        cat_input = CategoryInfo(new_category = new_category, subcategory = subcategory)
        session.add(cat_input)
        session.commit()

        if new_category == "" and subcategory == "":
            return render_template('/transactions.html', message = 'Please enter data on both fields')
       
        return render_template('/transactions.html', message = 'New categories added')
@app.route("/expense_graph", methods=['GET','POST'])
def expense_amt_data():
   
    i_expenses = {}
    
    expenses = session.query(func.round(func.sum(ExpenseInfo.expense_amt)), 
                func.month(ExpenseInfo.transaction_date)).\
                        group_by(func.month(ExpenseInfo.transaction_date))

    for e in expenses.all():
        i_expenses[e[1]] = str(e[0])
    data = {
        "expenses": i_expenses
    }
    
    return jsonify(data)

@app.route("/dash-summary")
def dash_summary():
    return render_template("dash-summary.html")

@app.route("/users-link")
def users_link():
    return render_template("users-link.html")

if __name__ == '__main__':
    app.debug = environ.get("DEBUG")
    app.run()




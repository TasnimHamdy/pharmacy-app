
from flask import Flask, render_template, request, redirect
import sqlite3
import datetime
import joblib

app = Flask(__name__)
model = joblib.load("models/classifier.pkl")

def classify_drug(name):
    return model.predict([name])[0]

def get_db_connection():
    conn = sqlite3.connect('pharmacy.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    drugs = conn.execute('SELECT * FROM drugs').fetchall()
    conn.close()

    today = datetime.date.today()
    warnings = []
    for drug in drugs:
        exp_date = datetime.datetime.strptime(drug['expiry'], '%Y-%m-%d').date()
        days_left = (exp_date - today).days
        if days_left <= 30:
            warnings.append((drug['name'], days_left))

    return render_template('index.html', drugs=drugs, warnings=warnings)

@app.route('/add', methods=('GET', 'POST'))
def add():
    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        production = request.form['production']
        expiry = request.form['expiry']
        category = classify_drug(name)

        conn = get_db_connection()
        conn.execute('INSERT INTO drugs (name, quantity, production, expiry, category) VALUES (?, ?, ?, ?, ?)',
                     (name, quantity, production, expiry, category))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('add.html')

if __name__ == '__main__':
    app.run(debug=True)

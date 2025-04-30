
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sqlite3
import os
import datetime
import pandas as pd
import joblib

# تحميل الموديل
try:
    model = joblib.load("models/classifier.pkl")
    vectorizer = joblib.load("models/vectorizer.pkl")
except:
    model = None
    vectorizer = None

DB_NAME = "pharmacy.db"
HIDE_WARNINGS = set()  # لتخزين الأدوية التي تم تجاهل تحذيرها مؤقتًا
# قاعدة البيانات
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS drugs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    quantity INTEGER,
                    production TEXT,
                    expiry TEXT,
                    category TEXT)''')
    conn.commit()
    conn.close()

def classify(name):
    if model and vectorizer:
        try:
            vec = vectorizer.transform([name])
            return model.predict(vec)[0]
        except:
            return "غير معروف"
    return "غير معروف"

def add_drug(name, quantity, production, expiry, category):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO drugs (name, quantity, production, expiry, category) VALUES (?, ?, ?, ?, ?)",
              (name, quantity, production, expiry, category))
    conn.commit()
    conn.close()
    refresh_data()

def update_drug(drug_id, name, quantity, production, expiry, category):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE drugs SET name=?, quantity=?, production=?, expiry=?, category=? WHERE id=?",
              (name, quantity, production, expiry, category, drug_id))
    conn.commit()
    conn.close()
    refresh_data()

def delete_drug(drug_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM drugs WHERE id=?", (drug_id,))
    conn.commit()
    conn.close()
    refresh_data()
def export_excel():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM drugs", conn)
    conn.close()
    file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if file:
        df.to_excel(file, index=False)
        messagebox.showinfo("تم", "تم تصدير البيانات إلى Excel بنجاح.")

def refresh_data():
    for row in tree.get_children():
        tree.delete(row)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    for row in c.execute("SELECT * FROM drugs"):
        tree.insert("", "end", values=row)
    conn.close()
    update_warnings()

def update_warnings():
    warning_text.set("")
    today = datetime.date.today()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    warnings = []
    for row in c.execute("SELECT id, name, expiry FROM drugs"):
        try:
            exp = datetime.datetime.strptime(row[2], "%Y-%m-%d").date()
            days_left = (exp - today).days
            if days_left <= 30 and row[0] not in HIDE_WARNINGS:
                warnings.append(f"{row[1]} (ينتهي خلال {days_left} يوم)")
        except:
            continue
    conn.close()
    if warnings:
        warning_text.set("⚠️ تنبيه: " + " | ".join(warnings))

def mark_reminded():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    for row in c.execute("SELECT id, expiry FROM drugs"):
        try:
            exp = datetime.datetime.strptime(row[1], "%Y-%m-%d").date()
            days_left = (exp - datetime.date.today()).days
            if days_left <= 30:
                HIDE_WARNINGS.add(row[0])
        except:
            continue
    update_warnings()
def open_form(edit=False):
    selected = tree.focus()
    form = tk.Toplevel(root)
    form.title("تعديل" if edit else "إضافة دواء")
    form.geometry("350x300")
    fields = ["الاسم", "الكمية", "تاريخ الإنتاج", "تاريخ الانتهاء", "النوع"]
    entries = []
    for f in fields:
        tk.Label(form, text=f).pack()
        entry = tk.Entry(form)
        entry.pack()
        entries.append(entry)

    if edit and selected:
        data = tree.item(selected)["values"]
        for i in range(5):
            entries[i].insert(0, data[i+1])

    def submit():
        vals = [e.get().strip() for e in entries]
        if not vals[4]:
            vals[4] = classify(vals[0])
        if edit:
            update_drug(tree.item(selected)["values"][0], *vals)
        else:
            add_drug(*vals)
        form.destroy()

    tk.Button(form, text="حفظ", command=submit).pack(pady=10)

def delete_selected():
    selected = tree.focus()
    if selected:
        result = messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا الدواء؟")
        if result:
            delete_drug(tree.item(selected)["values"][0])

# واجهة البرنامج
root = tk.Tk()
root.title("تطبيق الصيدلية")
root.geometry("900x500")

tk.Button(root, text="إضافة دواء", command=lambda: open_form(edit=False)).pack(side="top", pady=5)
tk.Button(root, text="تعديل", command=lambda: open_form(edit=True)).pack(side="top", pady=5)
tk.Button(root, text="حذف", command=delete_selected).pack(side="top", pady=5)
tk.Button(root, text="تصدير إلى Excel", command=export_excel).pack(side="top", pady=5)
tk.Button(root, text="تم التذكير ✅", command=mark_reminded).pack(side="top", pady=5)

warning_text = tk.StringVar()
tk.Label(root, textvariable=warning_text, fg="red").pack(pady=5)

cols = ["ID", "الاسم", "الكمية", "الإنتاج", "الانتهاء", "النوع"]
tree = ttk.Treeview(root, columns=cols, show="headings")
for col in cols:
    tree.heading(col, text=col)
tree.pack(fill="both", expand=True)

init_db()
refresh_data()
root.mainloop()

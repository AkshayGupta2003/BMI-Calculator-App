import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import bcrypt

def create_user_table():
    conn = sqlite3.connect("bmi_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            weight REAL,
            height REAL,
            bmi REAL,
            interpretation TEXT,
            search_history TEXT
        )
    """)
    conn.commit()
    conn.close()

def register_user():
    username = entry_username.get()
    password = entry_password.get()

    if username and password:
        conn = sqlite3.connect("bmi_database.db")
        cursor = conn.cursor()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("INSERT INTO users VALUES (?, ?, NULL, NULL, NULL, NULL, NULL)", (username, hashed_password))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "User registered successfully!")
    else:
        messagebox.showerror("Error", "Username and password are required.")

def login_user():
    global current_user
    username = entry_username.get()
    password = entry_password.get()

    if username and password:
        conn = sqlite3.connect("bmi_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data[1]):
            current_user = username
            user_combobox.set(current_user)
            switch_user()
            update_search_history()
            messagebox.showinfo("Success", "Login successful!")
        else:
            messagebox.showerror("Error", "Invalid username or password.")
    else:
        messagebox.showerror("Error", "Username and password are required.")

def switch_user():
    global current_user
    current_user = user_combobox.get()

    if current_user:
        conn = sqlite3.connect("bmi_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (current_user,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data:
            entry_weight.delete(0, tk.END)
            entry_weight.insert(0, user_data[2] if user_data[2] is not None else "")
            entry_height.delete(0, tk.END)
            entry_height.insert(0, user_data[3] if user_data[3] is not None else "")

def update_search_history():
    search_history_text.config(state=tk.NORMAL)
    search_history_text.delete("1.0", tk.END)

    if current_user:
        conn = sqlite3.connect("bmi_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT search_history FROM users WHERE username=?", (current_user,))
        search_history = cursor.fetchone()[0]
        conn.close()

        if search_history:
            history_list = eval(search_history)
            for entry in history_list:
                search_history_text.insert(tk.END, f"Weight: {entry['weight']}, Height: {entry['height']}\n")

    search_history_text.config(state=tk.DISABLED)

def calculate_bmi():
    try:
        weight = float(entry_weight.get())
        height = float(entry_height.get())

        if weight <= 0 or height <= 0:
            raise ValueError("Weight and height must be positive values.")

        bmi = weight / (height / 100) ** 2
        interpretation = interpret_bmi(bmi)

        result_label.config(text=f"Your BMI is: {bmi:.2f}\nInterpretation: {interpretation}")

        if current_user:
            conn = sqlite3.connect("bmi_database.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET weight=?, height=?, bmi=?, interpretation=?
                WHERE username=?
            """, (weight, height, bmi, interpretation, current_user))
            conn.commit()
            conn.close()

            conn = sqlite3.connect("bmi_database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT search_history FROM users WHERE username=?", (current_user,))
            search_history = cursor.fetchone()[0]
            conn.close()

            history_list = eval(search_history) if search_history else []
            history_list.append({"weight": weight, "height": height})

            conn = sqlite3.connect("bmi_database.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET search_history=?
                WHERE username=?
            """, (str(history_list), current_user))
            conn.commit()
            conn.close()

            update_search_history()
        else:
            messagebox.showerror("Error", "User not selected. Please log in.")

    except ValueError as e:
        messagebox.showerror("Error", str(e))

def interpret_bmi(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 24.9:
        return "Normal weight"
    elif 25 <= bmi < 29.9:
        return "Overweight"
    elif 30 <= bmi < 34.9:
        return "Obesity I"
    elif 35 <= bmi < 39.9:
        return "Obesity II"
    else:
        return "Obesity III"

def bookmark_bmi():
    if current_user:
        weight = entry_weight.get()
        height = entry_height.get()

        if weight and height:
            try:
                weight = float(weight)
                height = float(height)
                bmi = weight / (height / 100) ** 2
                interpretation = interpret_bmi(bmi)

                conn = sqlite3.connect("bmi_database.db")
                cursor = conn.cursor()
                cursor.execute("SELECT search_history FROM users WHERE username=?", (current_user,))
                search_history = cursor.fetchone()[0]
                conn.close()

                history_list = eval(search_history) if search_history else []
                history_list.append({"weight": weight, "height": height, "bmi": bmi, "interpretation": interpretation})

                conn = sqlite3.connect("bmi_database.db")
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET search_history=?
                    WHERE username=?
                """, (str(history_list), current_user))
                conn.commit()
                conn.close()

                update_search_history()
                messagebox.showinfo("Success", "BMI bookmarked successfully!")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showerror("Error", "Please enter weight and height before bookmarking.")
    else:
        messagebox.showerror("Error", "User not selected. Please log in.")

create_user_table()

app = tk.Tk()
app.title("BE-Fit Always")
app.geometry("400x550")
app.configure(background='#90EE90')

app.grid_columnconfigure(0, weight=1)

user_profiles = {
    "user1": {"password": bcrypt.hashpw(b"password1", bcrypt.gensalt()), "search_history": []},
    "user2": {"password": bcrypt.hashpw(b"password2", bcrypt.gensalt()), "search_history": []},
}

current_user = ""

label_username = ttk.Label(app, text="Username:")
entry_username = ttk.Entry(app)

label_password = ttk.Label(app, text="Password:")
entry_password = ttk.Entry(app, show="*")

register_button = ttk.Button(app, text="Register", command=register_user)
login_button = ttk.Button(app, text="Login", command=login_user)

label_user = ttk.Label(app, text="Select User:")
user_combobox = ttk.Combobox(app, values=list(user_profiles.keys()))
user_combobox.set(current_user)
user_combobox.bind("<<ComboboxSelected>>", lambda event: switch_user())

label_weight = ttk.Label(app, text="Enter your weight (kg):")
entry_weight = ttk.Entry(app)

label_height = ttk.Label(app, text="Enter your height (cm):")
entry_height = ttk.Entry(app)

calculate_button = ttk.Button(app, text="Calculate BMI", command=calculate_bmi)

result_label = ttk.Label(app, text="Result will be shown here.")
result_label.grid(row=9, column=0, pady=10, sticky="nsew")

label_history = ttk.Label(app, text="Search History:")
search_history_text = scrolledtext.ScrolledText(app, height=5, width=40, state=tk.DISABLED)

label_username.grid(row=0, column=0, padx=10, pady=10, sticky="W")
entry_username.grid(row=0, column=1, padx=10, pady=10)

label_password.grid(row=1, column=0, padx=10, pady=10, sticky="W")
entry_password.grid(row=1, column=1, padx=10, pady=10)

register_button.grid(row=2, column=0, columnspan=2, pady=10)
login_button.grid(row=3, column=0, columnspan=2, pady=10)

label_user.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="W")
user_combobox.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="EW")

label_weight.grid(row=6, column=0, padx=10, pady=10, sticky="W")
entry_weight.grid(row=6, column=1, padx=10, pady=10)

label_height.grid(row=7, column=0, padx=10, pady=10, sticky="W")
entry_height.grid(row=7, column=1, padx=10, pady=10)

calculate_button.grid(row=8, column=0, columnspan=2, pady=20)

bookmark_button = ttk.Button(app, text="Bookmark BMI", command=bookmark_bmi)
bookmark_button.grid(row=12, column=0, columnspan=2, pady=10)

label_history.grid(row=10, column=0, columnspan=2, padx=10, pady=10, sticky="W")
search_history_text.grid(row=11, column=0, columnspan=2, padx=10, pady=10)

app.mainloop()

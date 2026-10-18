
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

DB = "warehouse.db"


# ---------- DATABASE ----------
def connect_db():
    return sqlite3.connect(DB)


def setup_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                low_limit INTEGER NOT NULL DEFAULT 5
            )
        """)

        products = [
            ("Cardboard Boxes", 20, 5),
            ("Packing Tape", 12, 4),
            ("Electronic Components", 8, 3)
        ]

        conn.executemany("""
            INSERT OR IGNORE INTO inventory
            (name, quantity, low_limit)
            VALUES (?, ?, ?)
        """, products)


# ---------- INVENTORY DISPLAY ----------
def refresh():
    for item in table.get_children():
        table.delete(item)

    with connect_db() as conn:
        rows = conn.execute("""
            SELECT id, name, quantity, low_limit
            FROM inventory
            ORDER BY id
        """).fetchall()

    alerts = []

    for item_id, name, qty, limit in rows:
        status = "LOW STOCK" if qty <= limit else "Available"

        table.insert(
            "", "end",
            values=(item_id, name, qty, limit, status)
        )

        if qty <= limit:
            alerts.append(f"{name}: {qty} remaining")

    if alerts:
        alert_text.set("LOW-STOCK ALERT: " + " | ".join(alerts))
    else:
        alert_text.set("All products are above their low-stock limits.")


# ---------- STOCK IN / STOCK OUT ----------
def change_stock(action):
    name = name_var.get().strip()
    amount_text = amount_var.get().strip()

    if not name:
        messagebox.showerror("Input Error", "Enter a product name.")
        return

    try:
        amount = int(amount_text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror(
            "Input Error",
            "Quantity must be a positive whole number."
        )
        return

    with connect_db() as conn:
        row = conn.execute(
            "SELECT quantity FROM inventory WHERE name = ?",
            (name,)
        ).fetchone()

        if row is None:
            if action == "OUT":
                messagebox.showerror(
                    "Product Not Found",
                    "This product does not exist in inventory."
                )
                return

            conn.execute("""
                INSERT INTO inventory (name, quantity, low_limit)
                VALUES (?, ?, 5)
            """, (name, amount))

        else:
            current_qty = row[0]

            if action == "OUT" and amount > current_qty:
                messagebox.showerror(
                    "Insufficient Stock",
                    f"Only {current_qty} units are available."
                )
                return

            if action == "IN":
                new_qty = current_qty + amount
            else:
                new_qty = current_qty - amount

            conn.execute("""
                UPDATE inventory
                SET quantity = ?
                WHERE name = ?
            """, (new_qty, name))

    refresh()
    amount_var.set("")

    messagebox.showinfo(
        "Success",
        "Stock received successfully."
        if action == "IN"
        else "Stock dispatched successfully."
    )


# ---------- APPLICATION WINDOW ----------
setup_db()

root = tk.Tk()
root.title("Smart Warehouse Communication Network")
root.geometry("900x520")
root.minsize(750, 450)

tk.Label(
    root,
    text="SMART WAREHOUSE",
    font=("Arial", 22, "bold")
).pack(pady=(15, 3))

tk.Label(
    root,
    text="Inventory Management Dashboard",
    font=("Arial", 12)
).pack(pady=(0, 15))

form = tk.Frame(root)
form.pack(pady=5)

tk.Label(form, text="Product Name:").grid(
    row=0, column=0, padx=5, pady=5
)

name_var = tk.StringVar()

tk.Entry(
    form,
    textvariable=name_var,
    width=24
).grid(row=0, column=1, padx=5)

tk.Label(form, text="Quantity:").grid(
    row=0, column=2, padx=5
)

amount_var = tk.StringVar()

tk.Entry(
    form,
    textvariable=amount_var,
    width=10
).grid(row=0, column=3, padx=5)

tk.Button(
    form,
    text="Stock In",
    width=12,
    command=lambda: change_stock("IN")
).grid(row=0, column=4, padx=5)

tk.Button(
    form,
    text="Dispatch Stock",
    width=14,
    command=lambda: change_stock("OUT")
).grid(row=0, column=5, padx=5)

columns = ("ID", "Product", "Quantity", "Low Limit", "Status")

table = ttk.Treeview(
    root,
    columns=columns,
    show="headings",
    height=12
)

for column in columns:
    table.heading(column, text=column)
    table.column(column, width=160, anchor="center")

table.pack(fill="both", expand=True, padx=20, pady=15)

alert_text = tk.StringVar()

tk.Label(
    root,
    textvariable=alert_text,
    font=("Arial", 11, "bold"),
    wraplength=850
).pack(pady=8)

tk.Label(
    root,
    text="Database: SQLite | Smart Warehouse Inventory System",
    font=("Arial", 9)
).pack(pady=(0, 12))

refresh()
root.mainloop()

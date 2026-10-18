
from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
from pathlib import Path

app = Flask(__name__)
DB_PATH = Path(__file__).with_name("web_warehouse.db")

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Smart Warehouse Dashboard</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0; font-family: Arial, sans-serif;
            background: #f1f5f9; color: #172033;
        }
        header {
            background: #142b4a; color: white;
            padding: 24px 6%;
        }
        header h1 { margin: 0 0 8px; }
        header p { margin: 0; color: #cbd5e1; }
        main { max-width: 1100px; margin: 28px auto; padding: 0 18px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit,minmax(180px,1fr)); gap: 16px; }
        .card, .panel {
            background: white; padding: 20px; border-radius: 12px;
            box-shadow: 0 2px 10px #0f172a0d; margin-bottom: 20px;
        }
        .stat { font-size: 30px; font-weight: bold; margin-top: 10px; }
        .muted { color: #64748b; }
        .forms { display: grid; grid-template-columns: repeat(auto-fit,minmax(250px,1fr)); gap: 20px; }
        input, select, button {
            width: 100%; padding: 11px; margin: 7px 0;
            border: 1px solid #cbd5e1; border-radius: 7px; font-size: 15px;
        }
        button { background: #2563eb; color: white; border: 0; cursor: pointer; font-weight: bold; }
        button:hover { background: #1d4ed8; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 13px 10px; border-bottom: 1px solid #e2e8f0; text-align: left; }
        th { background: #f8fafc; }
        .low { color: #b91c1c; font-weight: bold; }
        .ok { color: #15803d; font-weight: bold; }
        .alert { padding: 12px; background: #fee2e2; color: #991b1b; border-radius: 8px; margin-bottom: 15px; }
        .notice { padding: 12px; background: #dcfce7; color: #166534; border-radius: 8px; margin-bottom: 15px; }
        footer { text-align: center; color: #64748b; padding: 25px; }
        @media (max-width: 600px) { table { font-size: 13px; } th, td { padding: 9px 5px; } }
    </style>
</head>
<body>
<header>
    <h1>Smart Warehouse</h1>
    <p>Communication Network · Live Inventory Management</p>
</header>
<main>
    {% if message %}
        <div class="notice">{{ message }}</div>
    {% endif %}

    <section class="stats">
        <div class="card"><div class="muted">Product Types</div><div class="stat">{{ products|length }}</div></div>
        <div class="card"><div class="muted">Total Units in Stock</div><div class="stat">{{ total }}</div></div>
        <div class="card"><div class="muted">Low-Stock Items</div><div class="stat">{{ low_count }}</div></div>
    </section>

    {% if low_count %}
        <div class="alert"><strong>Low-stock alert:</strong>
        {% for p in products if p.quantity <= p.low_limit %}
            {{ p.name }} ({{ p.quantity }} remaining){% if not loop.last %}; {% endif %}
        {% endfor %}
        </div>
    {% endif %}

    <section class="forms">
        <div class="panel">
            <h2>Stock In</h2>
            <form method="post" action="/stock-in">
                <label>Product</label>
                <select name="product_id" required>
                    {% for p in products %}<option value="{{ p.id }}">{{ p.name }}</option>{% endfor %}
                </select>
                <label>Quantity to add</label>
                <input type="number" name="quantity" min="1" required>
                <button type="submit">Add Stock</button>
            </form>
        </div>
        <div class="panel">
            <h2>Dispatch Stock</h2>
            <form method="post" action="/dispatch">
                <label>Product</label>
                <select name="product_id" required>
                    {% for p in products %}<option value="{{ p.id }}">{{ p.name }}</option>{% endfor %}
                </select>
                <label>Quantity to dispatch</label>
                <input type="number" name="quantity" min="1" required>
                <button type="submit">Dispatch</button>
            </form>
        </div>
    </section>

    <section class="panel">
        <h2>Inventory Overview</h2>
        <table>
            <thead><tr><th>Product</th><th>Quantity</th><th>Low Limit</th><th>Status</th></tr></thead>
            <tbody>
            {% for p in products %}
                <tr>
                    <td>{{ p.name }}</td><td>{{ p.quantity }}</td><td>{{ p.low_limit }}</td>
                    <td class="{{ 'low' if p.quantity <= p.low_limit else 'ok' }}">
                        {{ 'LOW STOCK' if p.quantity <= p.low_limit else 'In Stock' }}
                    </td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
    </section>
</main>
<footer>Smart Warehouse Communication Network · Project Demo</footer>
</body>
</html>
"""


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                quantity INTEGER NOT NULL DEFAULT 0,
                low_limit INTEGER NOT NULL DEFAULT 5
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO products (name, quantity, low_limit) VALUES (?, ?, ?)",
                [
                    ("Cardboard Boxes", 20, 5),
                    ("Packing Tape", 12, 4),
                    ("Electronic Components", 8, 3),
                ],
            )


def get_products():
    with connect_db() as conn:
        return conn.execute("SELECT * FROM products ORDER BY id").fetchall()


@app.route("/")
def index():
    products = get_products()
    message = request.args.get("message", "")
    return render_template_string(
        HTML,
        products=products,
        total=sum(p["quantity"] for p in products),
        low_count=sum(p["quantity"] <= p["low_limit"] for p in products),
        message=message,
    )


def update_stock(action):
    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", type=int)

    if not product_id or not quantity or quantity < 1:
        return redirect(url_for("index", message="Enter a valid quantity."))

    with connect_db() as conn:
        product = conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()

        if product is None:
            message = "Product not found."
        elif action == "dispatch" and quantity > product["quantity"]:
            message = "Dispatch rejected: insufficient stock."
        else:
            change = quantity if action == "stock-in" else -quantity
            conn.execute(
                "UPDATE products SET quantity = quantity + ? WHERE id = ?",
                (change, product_id),
            )
            message = "Stock updated successfully."

    return redirect(url_for("index", message=message))


@app.route("/stock-in", methods=["POST"])
def stock_in():
    return update_stock("stock-in")


@app.route("/dispatch", methods=["POST"])
def dispatch():
    return update_stock("dispatch")


init_db()

if __name__ == "__main__":
    app.run(debug=True)

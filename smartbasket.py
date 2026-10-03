"""SmartBasket - Intelligent Shopping Billing and Sales Analytics System
Core module: every task is a reusable function (Pandas + Matplotlib).
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, "sales.csv")

PRODUCTS = {  # product: (category, unit price in Rs)
    "Rice 5kg": ("Grocery", 320), "Wheat Flour 5kg": ("Grocery", 240),
    "Sugar 1kg": ("Grocery", 48), "Toor Dal 1kg": ("Grocery", 150),
    "Milk 1L": ("Dairy", 56), "Curd 500g": ("Dairy", 40), "Butter 100g": ("Dairy", 58),
    "Biscuits": ("Snacks", 30), "Chips": ("Snacks", 20), "Chocolate": ("Snacks", 50),
    "Soap": ("Personal Care", 38), "Shampoo": ("Personal Care", 120),
    "Toothpaste": ("Personal Care", 95), "Notebook": ("Stationery", 60),
    "Pen Pack": ("Stationery", 45),
}
GST = {"Grocery": 5, "Dairy": 5, "Snacks": 12, "Personal Care": 18, "Stationery": 12}


# ---------- data ----------
def generate_sample_data(rows=600, seed=42):
    """Create a sample sales dataset for the last 30 days and save it as sales.csv."""
    rng = np.random.default_rng(seed)
    names = list(PRODUCTS)
    weights = np.array([9, 6, 8, 5, 12, 6, 3, 10, 11, 7, 5, 3, 4, 3, 3], dtype=float)
    weights /= weights.sum()
    dates = pd.date_range("2026-09-03", periods=30)
    recs = []
    for i in range(rows):
        p = rng.choice(names, p=weights)
        recs.append({
            "bill_id": 1000 + i // 3,
            "date": rng.choice(dates),
            "product": p,
            "category": PRODUCTS[p][0],
            "quantity": int(rng.integers(1, 5)),
            "unit_price": PRODUCTS[p][1],
        })
    df = pd.DataFrame(recs)
    df["amount"] = df["quantity"] * df["unit_price"]
    df.to_csv(CSV_PATH, index=False)
    return df


def load_data():
    """Read sales.csv into a DataFrame (creates it first if missing)."""
    if not os.path.exists(CSV_PATH):
        generate_sample_data()
    df = pd.read_csv(CSV_PATH, parse_dates=["date"])
    return df


# ---------- billing ----------
def add_item(cart, product, qty):
    """Add a product and quantity to the cart (a list of dicts)."""
    category, price = PRODUCTS[product]
    cart.append({"product": product, "category": category,
                 "qty": qty, "price": price, "gst_pct": GST[category]})
    return cart


def calculate_bill(cart, discount_pct=0):
    """Return a bill DataFrame plus subtotal, GST, discount and grand total."""
    bill = pd.DataFrame(cart)
    bill["amount"] = bill["qty"] * bill["price"]
    bill["gst"] = (bill["amount"] * bill["gst_pct"] / 100).round(2)
    subtotal = bill["amount"].sum()
    gst_total = bill["gst"].sum()
    discount = round(subtotal * discount_pct / 100, 2)
    grand = round(subtotal + gst_total - discount, 2)
    return bill, {"subtotal": subtotal, "gst": round(gst_total, 2),
                  "discount": discount, "grand_total": grand}


def print_invoice(bill, totals, customer="Walk-in Customer", discount_pct=0):
    """Return the invoice as printable text."""
    line = "=" * 56
    out = [line, "            SMARTBASKET SUPERMARKET", "        Intelligent Billing Invoice", line,
           f"Customer : {customer}", "-" * 56,
           f"{'Item':<18}{'Qty':>4}{'Price':>8}{'GST%':>6}{'Amount':>10}", "-" * 56]
    for _, r in bill.iterrows():
        out.append(f"{r['product']:<18}{r['qty']:>4}{r['price']:>8}{r['gst_pct']:>6}{r['amount']:>10.2f}")
    out += ["-" * 56,
            f"{'Subtotal':<40}{totals['subtotal']:>16.2f}",
            f"{'GST':<40}{totals['gst']:>16.2f}",
            f"{'Discount (' + str(discount_pct) + '%)':<40}{-totals['discount']:>16.2f}",
            line, f"{'GRAND TOTAL (Rs)':<40}{totals['grand_total']:>16.2f}", line,
            "        Thank you! Visit again."]
    return "\n".join(out)


# ---------- analysis ----------
def top_products(df, n=5):
    return df.groupby("product")["amount"].sum().sort_values(ascending=False).head(n)


def daily_sales(df):
    return df.groupby("date")["amount"].sum()


def category_sales(df):
    return df.groupby("category")["amount"].sum().sort_values(ascending=False)


def summary(df):
    return {"total_revenue": int(df["amount"].sum()),
            "bills": int(df["bill_id"].nunique()),
            "items_sold": int(df["quantity"].sum()),
            "best_product": top_products(df, 1).index[0],
            "best_day": daily_sales(df).idxmax().strftime("%d %b %Y")}


# ---------- charts ----------
def plot_chart(kind, df, path=None, n=5):
    """kind: 'top' (bar), 'daily' (line), 'category' (pie). Returns a Matplotlib figure."""
    fig, ax = plt.subplots(figsize=(7, 4.2))
    if kind == "top":
        s = top_products(df, n)[::-1]
        ax.barh(s.index, s.values, color="#2E7D32")
        ax.set_title(f"Top {n} Products by Revenue"); ax.set_xlabel("Revenue (Rs)")
    elif kind == "daily":
        s = daily_sales(df)
        ax.plot(s.index, s.values, marker="o", color="#1565C0")
        ax.set_title("Daily Sales Trend"); ax.set_ylabel("Revenue (Rs)")
        fig.autofmt_xdate()
    elif kind == "category":
        s = category_sales(df)
        ax.pie(s.values, labels=s.index, autopct="%1.1f%%", startangle=90)
        ax.set_title("Revenue Share by Category")
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=150)
    return fig


# ---------- chatbot ----------
def chatbot_reply(question, df):
    """Keyword matching: returns (text answer, chart kind or None)."""
    q = question.lower()
    if any(k in q for k in ["top", "best", "popular"]):
        n = 5
        for w in q.split():
            if w.isdigit():
                n = int(w)
        s = top_products(df, n)
        txt = f"Top {n} products by revenue:\n" + "\n".join(f"{i+1}. {k} - Rs {v:,}" for i, (k, v) in enumerate(s.items()))
        return txt, "top"
    if "categor" in q:
        s = category_sales(df)
        return "Revenue by category:\n" + "\n".join(f"{k}: Rs {v:,}" for k, v in s.items()), "category"
    if any(k in q for k in ["daily", "day", "trend"]):
        s = daily_sales(df)
        return f"Best day: {s.idxmax().strftime('%d %b')} (Rs {s.max():,}). Average per day: Rs {int(s.mean()):,}.", "daily"
    if any(k in q for k in ["total", "revenue", "sales"]):
        return f"Total revenue is Rs {int(df['amount'].sum()):,} from {df['bill_id'].nunique()} bills.", None
    return "Try: 'top 5 products', 'category sales', 'daily trend' or 'total revenue'.", None

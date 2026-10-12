import sqlite3
from pathlib import Path
from datetime import date, timedelta
from pprint import pprint

db_file = Path(__file__).parent / 'support.db'

def setup_db():
    db_connection = sqlite3.connect(db_file)
    db_connection.row_factory = sqlite3.Row

    cursor = db_connection.cursor()

    # create a db rows and columns
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        item TEXT NOT NULL,
        amount TEXT,
        delivered_on TEXT)
        """
    )

    today = date.today()

    row = [
        (1234, 'prosper', 20, 'book', '$30', today - timedelta(days=10)),
        (1235, 'daniel', 40, 'T-shirt', '$40', today - timedelta(days=5)),
        (1236, 'esther', 50, 'Sleeves', '$70', today - timedelta(days=8)),
        (1237, 'prince', 80, 'Trousers', '$90', today - timedelta(days=9))
    ]

    # loop over the rows to append the items one by one
    rows = []
    for i, n, a, it, am, d in row:
        if d:
            date_value = d.isoformat()
        else:
            date_value = None
        rows.append((i, n, a, it, am, date_value))

    cursor.executemany(
        """
        INSERT INTO users (id, name, age, item, amount, delivered_on)
        VALUES (?, ?, ?, ?, ?, ?)
        """, rows
    )
    db_connection.commit()

    # data = cursor.execute(
    #     """
    #     SELECT * FROM users  where id = 1234
    #     """
    # ).fetchall()

    # [pprint([dict(row)]) for row in data]

    return db_connection

db_conn = setup_db()

# refresh the db for each time the db is called
def refresh_db()-> None:
    global db_conn
    db_conn.close()
    db_conn.setup_up()
    
def _clean_id(order_id):
    return int(str(order_id).strip().lstrip('#'))

def lookup_order(order_id) -> dict:
    # perform the SQL operation to get the order by id
    row = db_conn.execute("""
    SELECT * FROM users WHERE id = ?
    """, (_clean_id(order_id),)).fetchone()
    if row is None:
        return {"found": False, "error": "No order with the id given"}
    #returns the order as a row
    order = dict(row)
    print(order)
    if order['delivered_on']:
        days = (date.today() - date.fromisoformat(order['delivered_on'])).days
        # create a new key_value pair here to store the days_since_delivery
        order['days_since_delivery'] = days
    return {"found": True, "order": order}

def refund_policy()-> dict:
    return {
        "refund_window_days": REFUND_WINDOW_DAYS,
        "rules": [
            f"Refunds are allowed within {REFUND_WINDOW_DAYS} days of delivery.",
            "Damaged or defective items are eligible within the window.",
            "Orders not yet delivered cannot be refunded (they can be cancelled instead).",
            "Orders already refunded cannot be refunded again.",
            "The refund cannot exceed the order amount.",
        ],
    }





out = lookup_order('#1239')
print(out)





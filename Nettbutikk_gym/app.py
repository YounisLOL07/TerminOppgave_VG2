from flask import Flask, render_template, redirect, url_for, session, request
import sqlite3


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Simulated product data
products = [
    {'id': 1, 'name': 'Creatine', 'price': 19.99, 'image': 'images/creatine_skull.png', 'info': "For juicy pumps!"},
    {'id': 2, 'name': 'Pre-Workout', 'price': 24.99, 'image': 'images/pre-workout_skull.png', 'info': "To energies you workouts!"},
    {'id': 3, 'name': 'Protein Powder', 'price': 29.99, 'image': 'images/protein_powder_skull.png', 'info': "To hit your protein goals!"}
]

def get_db_connection():
    conn = sqlite3.connect('store.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html', products=products)

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/product/<int:product_id>')
def product_details(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return "Product not found", 404
    return render_template('product_details.html', product=product)


@app.context_processor
def inject_cart_count():
    cart_count = sum(item['quantity'] for item in session.get('cart', []))
    return {'cart_count': cart_count}

@app.route('/add_to_cart/<int:product_id>', methods=['GET', 'POST'])
def add_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))  # Default quantity is 1
    if 'cart' not in session:
        session['cart'] = []

    # Check if the product is already in the cart
    product_in_cart = next((item for item in session['cart'] if item['id'] == product_id), None)
    if product_in_cart:
        product_in_cart['quantity'] += quantity
    else:
        session['cart'].append({'id': product_id, 'quantity': quantity})

    session.modified = True
    return redirect(url_for('cart'))


@app.route('/cart')
def cart():
    cart_items = []
    total_price = 0

    if 'cart' in session:
        for item in session['cart']:
            product = next((product for product in products if product['id'] == item['id']), None)
            if product:
                product_with_quantity = product.copy()
                product_with_quantity['quantity'] = item['quantity']
                cart_items.append(product_with_quantity)
                total_price += product['price'] * item['quantity']

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        cart = session.get('cart', [])
        if not cart:
            return redirect(url_for('cart'))

        # Calculate the total price
        total_price = sum(
            next(product['price'] for product in products if product['id'] == item['id']) * item['quantity']
            for item in cart
        )

        # Prepare receipt data
        receipt = {
            'total_price': round(total_price, 2),
            'date': 'Now',  # You can replace 'Now' with a real timestamp if desired
            'items': [
                {
                    'name': next(product['name'] for product in products if product['id'] == item['id']),
                    'quantity': item['quantity'],
                    'price': round(next(product['price'] for product in products if product['id'] == item['id']), 2)
                }
                for item in cart
            ]
        }

        # Clear the cart after checkout
        session.pop('cart', None)

        # Pass the receipt data to the receipt page
        return render_template('receipt.html', receipt=receipt)

    return render_template('checkout.html')


@app.route('/receipt/<int:receipt_id>')
def receipt(receipt_id):
    conn = get_db_connection()
    receipt = conn.execute('SELECT * FROM receipts WHERE id = ?', (receipt_id,)).fetchone()
    receipt_items = conn.execute('''
        SELECT products.name, products.price, receipt_items.quantity
        FROM receipt_items
        JOIN products ON receipt_items.product_id = products.id
        WHERE receipt_items.receipt_id = ?
    ''', (receipt_id,)).fetchall()
    conn.close()
    return render_template('receipt.html', receipt=receipt, receipt_items=receipt_items)

if __name__ == '__main__':
    app.run(debug=True)

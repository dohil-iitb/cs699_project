from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import time
import random
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = '25m0836'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medicines.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    watchlist = db.relationship('Watchlist', backref='user', lazy=True)


class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medicine_name = db.Column(db.String(200), nullable=False)
    added_date = db.Column(db.DateTime, default=datetime.utcnow)


class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicine_name = db.Column(db.String(200), nullable=False)
    source = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    availability = db.Column(db.String(50), nullable=False)
    recorded_date = db.Column(db.DateTime, default=datetime.utcnow)


# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")


init_db()


# Setup Selenium driver
def get_driver():
    """Create and return a headless Firefox driver"""
    options = Options()
    options.binary_location = "/snap/firefox/current/usr/lib/firefox/firefox"
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Firefox(options=options)
    return driver


def extract_price(text):
    """Extract price from text"""
    if not text:
        return None

    numbers = re.findall(r'\d+\.?\d*', text)
    if numbers:
        return float(numbers[0])
    return None

def scrape_apollo(medicine_name):

    """Scrape Apollo Pharmacy using Selenium"""
    driver = None
    try:
        print(f"Scraping Apollo for: {medicine_name}")
        driver = get_driver()

        # Format URL
        medicine_formatted = medicine_name.lower().replace(' ', '-')
        search_url = f"https://www.apollopharmacy.in/search-medicines/{medicine_formatted}"

        driver.get(search_url)
        time.sleep(3)  # Wait for page load

        # Find all product containers (adjust selector based on actual HTML structure)
        product_containers = driver.find_elements(By.XPATH,
                                                  "//div[contains(@class, 'product-card') or contains(@class, 'product-item') or contains(@class, 'ProductCard')]")

        results = []

        if not product_containers:
            # Fallback: try to find any container with both name and price
            product_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'product')]")

        print(f"Found {len(product_containers)} potential products")

        for idx, container in enumerate(product_containers, 1):
            try:
                # Extract product name from within this container
                product_name = None
                name_selectors = [
                    ".//h1 | .//h2 | .//h3",
                    ".//*[contains(@class, 'product-name')]",
                    ".//*[contains(@class, 'title')]",
                    ".//a[contains(@class, 'product')]"
                ]

                for selector in name_selectors:
                    try:
                        name_elem = container.find_element(By.XPATH, selector)
                        product_name = name_elem.text.strip()
                        if product_name:
                            break
                    except:
                        continue

                # Extract price from within the SAME container
                price = None
                price_selectors = [
                    ".//span[contains(@class, 'price')]",
                    ".//span[contains(text(), '₹')]",
                    ".//div[contains(@class, 'price')]//span",
                    ".//*[contains(text(), 'Rs')]"
                ]

                for selector in price_selectors:
                    try:
                        price_elem = container.find_element(By.XPATH, selector)
                        price_text = price_elem.text
                        price = extract_price(price_text)
                        if price:
                            break
                    except:
                        continue

                # Check availability within this container
                availability = 'In Stock'
                try:
                    container.find_element(By.XPATH,
                                           ".//*[contains(text(), 'Out of Stock') or contains(text(), 'out of stock')]")
                    availability = 'Out of Stock'
                except:
                    pass

                # Only add if we found both name and price
                if product_name and price:
                    full_product_name = f"{product_name} - Apollo Pharmacy"
                    results.append({
                        'product_name': full_product_name,
                        'price': price,
                        'availability': availability,
                        'source': 'Apollo Pharmacy'
                    })
                    print(f"✓ Product {idx}: {full_product_name} - ₹{price} ({availability})")
                else:
                    print(f"✗ Product {idx}: Skipped (Name: {bool(product_name)}, Price: {bool(price)})")

            except Exception as e:
                print(f"Error processing container {idx}: {e}")
                continue

        if results:
            print(f"\n✓ Apollo: Found {len(results)} valid products")
            return results  # Return ALL results

        print("Apollo: No valid products found")
        return None

    except Exception as e:
        print(f"Apollo error: {e}")
        return None
    finally:
        if driver:
            driver.quit()


def search_medicine(medicine_name):
    """Search both pharmacies and return results"""
    results = []

    # Try Apollo
    apollo_results = scrape_apollo(medicine_name)
    for apollo_result in apollo_results:
        if apollo_result:
            results.append(apollo_result)
            price_record = PriceHistory(
                medicine_name=apollo_result['product_name'].split(" - Apollo Pharmacy")[0].strip(),
                source='Apollo',
                price=apollo_result['price'],
                availability=apollo_result['availability']
            )
            db.session.add(price_record)

    #
    # medplus_result = scrape_medplus(medicine_name)
    # if medplus_result:
    #     results.append(medplus_result)
    #     price_record = PriceHistory(
    #         medicine_name=medicine_name,
    #         source='MedPlus',
    #         price=medplus_result['price'],
    #         availability=medplus_result['availability']
    #     )
    #     db.session.add(price_record)

    db.session.commit()
    return results


def generate_price_graph(medicine_name):
    """Generate price trend graph"""
    history = PriceHistory.query.filter_by(medicine_name=medicine_name).order_by(PriceHistory.recorded_date).all()

    if not history:
        return None

    # Separate data by source
    apollo_dates, apollo_prices = [], []
    medplus_dates, medplus_prices = [], []

    for record in history:
        if record.source == 'Apollo':
            apollo_dates.append(record.recorded_date)
            apollo_prices.append(record.price)
        else:
            medplus_dates.append(record.recorded_date)
            medplus_prices.append(record.price)

    # Create plot
    plt.figure(figsize=(10, 6))

    if apollo_dates:
        plt.plot(apollo_dates, apollo_prices, marker='o', label='Apollo Pharmacy', linewidth=2)

    if medplus_dates:
        plt.plot(medplus_dates, medplus_prices, marker='s', label='MedPlus', linewidth=2)

    plt.xlabel('Date')
    plt.ylabel('Price (₹)')
    plt.title(f'Price Trend for {medicine_name}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()

    graphic = base64.b64encode(image_png).decode('utf-8')
    return graphic


# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))

        return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    watchlist_items = Watchlist.query.filter_by(user_id=user.id).all()

    return render_template('dashboard.html', user=user, watchlist=watchlist_items)


@app.route('/search', methods=['POST'])
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    medicine_name = request.form['medicine_name']
    results = search_medicine(medicine_name)

    return render_template('search_results.html', medicine_name=medicine_name, results=results)


@app.route('/add_to_watchlist/<medicine_name>')
def add_to_watchlist(medicine_name):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    existing = Watchlist.query.filter_by(user_id=session['user_id'], medicine_name=medicine_name).first()

    if not existing:
        watchlist_item = Watchlist(user_id=session['user_id'], medicine_name=medicine_name)
        db.session.add(watchlist_item)
        db.session.commit()

    return redirect(url_for('dashboard'))


@app.route('/remove_from_watchlist/<int:item_id>')
def remove_from_watchlist(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    item = Watchlist.query.get(item_id)
    if item and item.user_id == session['user_id']:
        db.session.delete(item)
        db.session.commit()

    return redirect(url_for('dashboard'))


@app.route('/price_trend/<medicine_name>')
def price_trend(medicine_name):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    graph = generate_price_graph(medicine_name)

    return render_template('price_trend.html', medicine_name=medicine_name, graph=graph)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
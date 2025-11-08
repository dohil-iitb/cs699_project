from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import db, User, Drug, DrugPrice
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///drug_prices.db'

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Mock data for demonstration (replace with your web scraping results)
def get_mock_drug_data():
    return [
        {
            'name': 'Aspirin 100mg',
            'prices': [
                {'pharmacy': 'CVS Pharmacy', 'price': 5.99, 'availability': True},
                {'pharmacy': 'Walgreens', 'price': 4.99, 'availability': True},
                {'pharmacy': 'Walmart', 'price': 3.99, 'availability': True},
                {'pharmacy': 'Rite Aid', 'price': 6.49, 'availability': False}
            ]
        },
        {
            'name': 'Metformin 500mg',
            'prices': [
                {'pharmacy': 'CVS Pharmacy', 'price': 15.99, 'availability': True},
                {'pharmacy': 'Walgreens', 'price': 12.99, 'availability': True},
                {'pharmacy': 'Walmart', 'price': 9.99, 'availability': True},
                {'pharmacy': 'Rite Aid', 'price': 16.49, 'availability': True}
            ]
        }
    ]

def analyze_drug_prices(drug_data):
    analysis = {}
    for drug in drug_data:
        available_prices = [p for p in drug['prices'] if p['availability']]
        if available_prices:
            best_price = min(available_prices, key=lambda x: x['price'])
            avg_price = sum(p['price'] for p in available_prices) / len(available_prices)
            
            analysis[drug['name']] = {
                'best_price': best_price,
                'average_price': round(avg_price, 2),
                'total_pharmacies': len(drug['prices']),
                'available_pharmacies': len(available_prices),
                'recommendation': 'Good Deal' if best_price['price'] < avg_price * 0.8 else 'Average Price'
            }
    return analysis

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        drug_name = request.form['drug_name']
        
        # Mock data - replace with your actual data retrieval
        drug_data = get_mock_drug_data()
        filtered_drugs = [drug for drug in drug_data if drug_name.lower() in drug['name'].lower()]
        
        if filtered_drugs:
            analysis = analyze_drug_prices(filtered_drugs)
            return render_template('results.html', 
                                 drug_data=filtered_drugs, 
                                 analysis=analysis,
                                 search_term=drug_name)
        else:
            flash('No drugs found matching your search.', 'error')
    
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# API endpoint for drug data (for future enhancements)
@app.route('/api/drugs/<drug_name>')
def get_drug_data(drug_name):
    drug_data = get_mock_drug_data()
    filtered_drugs = [drug for drug in drug_data if drug_name.lower() in drug['name'].lower()]
    return jsonify(filtered_drugs)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
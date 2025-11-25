#!/usr/bin/env python3

from app import app, db, User, Watchlist, PriceHistory
from werkzeug.security import generate_password_hash


def init_database():
    """Initialize the database and create all tables"""
    with app.app_context():
        # Drop all existing tables (use with caution!)
        print("Dropping existing tables...")
        db.drop_all()

        # Create all tables
        print("Creating database tables...")
        db.create_all()

        print("Database tables created successfully!")
        print("\nTables created:")
        print("  - users")
        print("  - watchlist")
        print("  - price_history")

        # # Optionally create a demo user
        # create_demo = input("\nCreate a demo user? (y/n): ").lower()
        # if create_demo == 'y':
        #     demo_username = input("Enter username (default: demo): ") or "demo"
        #     demo_password = input("Enter password (default: demo123): ") or "demo123"
        #
        #     # Check if user already exists
        #     existing_user = User.query.filter_by(username=demo_username).first()
        #     if existing_user:
        #         print(f"User '{demo_username}' already exists!")
        #     else:
        #         demo_user = User(
        #             username=demo_username,
        #             password=generate_password_hash(demo_password)
        #         )
        #         db.session.add(demo_user)
        #         db.session.commit()
        #         print(f"✓ Demo user created: {demo_username}")
        #
        # print("\n✅ Database initialization complete!")
        # print("You can now run the app with: python3 app.py")


if __name__ == "__main__":
    print("=" * 50)
    print("Medicine Price Tracker - Database Setup")
    print("=" * 50)
    print("\nThis will create/reset the database.")

    confirm = input("Continue? (y/n): ").lower()
    if confirm == 'y':
        init_database()
    else:
        print("Database initialization cancelled.")
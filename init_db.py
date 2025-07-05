"""
Database initialization script for the trading bot.
This script initializes the database tables and can be used to reset the database if needed.
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import argparse
from db_config import DATABASE_URL, engine, Base

def create_tables():
    """Create all tables in the database"""
    try:
        import models
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False

def init_database(reset=False):
    """Initialize the database"""
    try:
        # Check if database exists, if not create it
        if not database_exists(DATABASE_URL):
            create_database(DATABASE_URL)
        else:
            print(f"ℹ️ Database already exists at {DATABASE_URL}")
        
        if reset:
            # Drop all tables if reset is True
            Base.metadata.drop_all(bind=engine)
            print("🗑️ Dropped all existing tables")
        
        # Create tables
        success = create_tables()
        
        return success
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Initialize the trading bot database')
    parser.add_argument('--reset', action='store_true', help='Reset the database by dropping all tables first')
    args = parser.parse_args()
    
    success = init_database(reset=args.reset)
    
    if not success:
        print("❌ Database initialization failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

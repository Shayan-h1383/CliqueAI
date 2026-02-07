#!/usr/bin/env python
"""Check if MongoDB is running and accessible."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def check_mongodb():
    """Verify MongoDB connection."""
    uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure
        
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        print(f"✓ MongoDB is running and accessible at {uri}")
        return True
    except ConnectionFailure as e:
        print(f"✗ MongoDB connection failed: {e}", file=sys.stderr)
        print("\nTo set up MongoDB:", file=sys.stderr)
        print("  1. Install MongoDB: https://www.mongodb.com/try/download/community", file=sys.stderr)
        print("  2. Start the service: mongod (or 'net start MongoDB' on Windows)", file=sys.stderr)
        print("  3. Copy .env.example to .env and set MONGODB_URI", file=sys.stderr)
        return False

if __name__ == '__main__':
    sys.exit(0 if check_mongodb() else 1)

"""
EventCore – Application Entrypoint
Run this script from the project root:
    python run.py
"""

import sys, os

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.models   import init_db
from backend.db_setup import seed
from backend.app      import app

if __name__ == "__main__":
    # First-run: create tables and seed data if DB doesn't exist
    db_path = os.path.join(os.path.dirname(__file__), "backend", "database.db")
    first_run = not os.path.exists(db_path)

    init_db()

    if first_run:
        print("First run detected – seeding database with 15 mock registrations...")
        seed(send_emails=True)

    print("\n" + "="*55)
    print("  EventCore Full-Stack Server")
    print("  URL : http://localhost:5000")
    print("  API : http://localhost:5000/api/")
    print("="*55 + "\n")

    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

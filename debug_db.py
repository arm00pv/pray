from app import app, db
import os

if os.path.exists('praying_diary.db'):
    os.remove('praying_diary.db')

with app.app_context():
    db.create_all()
    print("DB Created")
    from models import Admin
    # check columns
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('admin')]
    print(f"Admin columns: {columns}")

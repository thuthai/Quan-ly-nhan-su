from app import app, db
from sqlalchemy import Column, String, text

# Define migration function
def migrate():
    with app.app_context():
        # Add id_card_number column to employee table
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE employee ADD COLUMN id_card_number VARCHAR(20) UNIQUE'))
            conn.commit()
        print("Migration completed successfully: Added id_card_number to employee table")

if __name__ == "__main__":
    migrate()
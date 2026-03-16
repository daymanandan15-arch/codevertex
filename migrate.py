import sqlite3
import time

def migrate():
    # Retry logic if db is locked
    for i in range(5):
        try:
            conn = sqlite3.connect('engineering_portal.db', timeout=10.0)
            c = conn.cursor()
            
            # Post Bounty
            try:
                c.execute('ALTER TABLE posts ADD COLUMN bounty INTEGER DEFAULT 0')
                print('Added bounty to posts')
            except sqlite3.OperationalError:
                pass
                
            # Mentor Fields
            try:
                c.execute('ALTER TABLE users ADD COLUMN is_mentor BOOLEAN DEFAULT 0')
                print('Added is_mentor to users')
            except sqlite3.OperationalError:
                pass
                
            try:
                c.execute('ALTER TABLE users ADD COLUMN mentor_bio TEXT')
                print('Added mentor_bio to users')
            except sqlite3.OperationalError:
                pass
                
            conn.commit()
            conn.close()
            print('Migration SUCCESS')
            return
        except Exception as e:
            print(f'Attempt {i+1} failed: {e}')
            time.sleep(1)

migrate()

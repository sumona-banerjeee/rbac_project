from database import SessionLocal
from models import Announcement

db = SessionLocal()
rows = db.query(Announcement).all()
print(f"Total announcements: {len(rows)}")
for a in rows:
    print(a.id, a.title)
db.close()

from app.database.session import sync_engine
from sqlalchemy import text, inspect

inspector = inspect(sync_engine)
tables = inspector.get_table_names()
print("Tables:", tables)

with sync_engine.connect() as conn:
    users = conn.execute(text("SELECT email, role FROM users")).fetchall()
    print("Users:", [(u[0], u[1]) for u in users])
    
    clients = conn.execute(text("SELECT business_name FROM clients")).fetchall()
    print("Clients:", [c[0] for c in clients])
    
    invs = conn.execute(text("SELECT title, status FROM investigations")).fetchall()
    print("Investigations:", [(i[0], i[1]) for i in invs])

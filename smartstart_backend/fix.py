import sys
sys.path.append(r'C:\Users\user\Desktop\BIIA\BiAi\Service_ml\models3\code')
from service.db import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.connect() as conn:
    conn.execute(text("""
        UPDATE companies 
        SET beta=0.9, net_debt=50000, ebitda_margins=0.15, revenue_per_employee=350000 
        WHERE name='SOAFT'
    """))
    conn.execute(text("DELETE FROM companies WHERE name='string'"))
    conn.commit()
    print('Done')
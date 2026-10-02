from service.db import fetch_data

tables = fetch_data("""
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
""")

print(tables)
#!/usr/bin/env python3
"""
Import work schedule from MEMORY.md into PostgreSQL
"""
import subprocess, re
from datetime import date

def sql(q):
    subprocess.run(['docker', 'exec', 'pgvector_db', 'psql', '-U', 'jhe', '-d', 'openclaw', '-c', q], capture_output=True)

def parse_schedule():
    """Parse 5/6 month schedule from MEMORY.md"""
    entries = []
    
    # 5月 schedule
    may_data = [
        ('2026-05-21', '15:00', '21:00', 5.5, False, ''),
        ('2026-05-22', '17:00', '21:00', 4.0, False, ''),
        ('2026-05-25', None, None, 0, True, '休假日'),
        ('2026-05-26', '17:00', '21:00', 4.0, False, ''),
        ('2026-05-27', '13:00', '21:00', 7.5, False, ''),
        ('2026-05-29', '13:00', '21:00', 7.5, False, ''),
        ('2026-05-30', '11:00', '21:00', 9.0, False, ''),
    ]
    
    # 6月 schedule
    june_data = [
        ('2026-06-01', '17:00', '21:00', 4.0, False, ''),
        ('2026-06-02', '13:00', '21:00', 7.5, False, ''),
        ('2026-06-05', '17:00', '21:00', 4.0, False, ''),
        ('2026-06-06', '13:00', '21:00', 7.5, False, ''),
    ]
    
    return may_data + june_data

def etl():
    entries = parse_schedule()
    
    # Clear old data
    sql("DELETE FROM work_schedule;")
    print(f"[ETL] Importing {len(entries)} schedule entries...")
    
    for (work_date, start, end, hours, is_holiday, notes) in entries:
        start_val = f"'{start}'" if start else 'NULL'
        end_val = f"'{end}'" if end else 'NULL'
        notes_val = f"'{notes}'" if notes else 'NULL'
        sql(f"""
            INSERT INTO work_schedule (work_date, start_time, end_time, work_hours, is_holiday, notes)
            VALUES ('{work_date}', {start_val}, {end_val}, {hours}, {is_holiday}, {notes_val});
        """)
    
    # Verify
    r = subprocess.run(['docker', 'exec', 'pgvector_db', 'psql', '-U', 'jhe', '-d', 'openclaw', '-t', '-c', 
        "SELECT work_date, start_time, end_time, work_hours, is_holiday FROM work_schedule ORDER BY work_date;"],
        capture_output=True, text=True)
    print(r.stdout)
    print("[ETL] Done")

if __name__ == '__main__':
    etl()
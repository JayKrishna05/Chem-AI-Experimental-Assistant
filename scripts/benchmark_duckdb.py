import time
from backend.tools.db import connect_read_only

def test_count_strategies():
    with connect_read_only() as con:
        # Strategy A: Separate SELECT COUNT(*)
        start = time.perf_counter()
        count_cur = con.execute("SELECT COUNT(*) FROM reactions")
        total = count_cur.fetchone()[0]
        rows_cur = con.execute("SELECT reaction_id FROM reactions LIMIT 10")
        rows = rows_cur.fetchall()
        t_a = time.perf_counter() - start
        
        # Strategy B: COUNT(*) OVER() Window Function
        start = time.perf_counter()
        cur = con.execute("SELECT reaction_id, COUNT(*) OVER() as total FROM reactions LIMIT 10")
        rows_b = cur.fetchall()
        t_b = time.perf_counter() - start
        
        print(f"Strategy A (Separate Count): {t_a*1000:.2f}ms | Total: {total}")
        print(f"Strategy B (Window Function): {t_b*1000:.2f}ms | Total: {rows_b[0][1]}")

test_count_strategies()

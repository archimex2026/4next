"""Bound expensive work by account; shared SQLite budgets and local in-flight slots."""
import threading
import time
from contextlib import closing, contextmanager
from fastapi import HTTPException
from app.database import get_db_connection

LIMITS = {"upload": ((60, 5), (86400, 30)), "audio": ((60, 3), (86400, 20)), "inspect": ((60, 10),)}
_slots = threading.BoundedSemaphore(3)
_lock = threading.Lock()
_active_users = set()


def consume_budget(user_id, operation):
    now = int(time.time())
    with closing(get_db_connection()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute("DELETE FROM generation_usage WHERE bucket * period < ?", (now - 7 * 86400,))
            for period, maximum in LIMITS[operation]:
                bucket = now // period
                row = conn.execute("SELECT requests FROM generation_usage WHERE user_id=? AND operation=? AND period=? AND bucket=?",
                    (user_id, operation, period, bucket)).fetchone()
                if row and row["requests"] >= maximum:
                    raise HTTPException(429, "Ai atins limita de utilizare pentru această funcție. Încearcă mai târziu.",
                        headers={"Retry-After": str(period - now % period)})
                conn.execute("""INSERT INTO generation_usage(user_id,operation,period,bucket,requests) VALUES(?,?,?,?,1)
                    ON CONFLICT(user_id,operation,period,bucket) DO UPDATE SET requests=requests+1""",
                    (user_id, operation, period, bucket))
            conn.commit()
        except Exception:
            conn.rollback()
            raise


@contextmanager
def generation_slot(user_id, operation):
    # ponytail: process-local concurrency; a distributed queue is needed for multiple API workers.
    with _lock:
        if user_id in _active_users or not _slots.acquire(blocking=False):
            raise HTTPException(429, "O generare este deja în lucru. Încearcă din nou după finalizare.", headers={"Retry-After": "10"})
        _active_users.add(user_id)
    try:
        consume_budget(user_id, operation)
        yield
    finally:
        with _lock:
            _active_users.remove(user_id)
            _slots.release()

import os
import csv
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger("BeeLogger")


class LoggerManager:
    """Manages offline event logging to local SQLite database and CSV file."""

    def __init__(self, db_path="data/bee_logs.sqlite", csv_path="data/bee_logs.csv"):
        self.db_path = db_path
        self.csv_path = csv_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        self._init_db()
        self._init_csv()

    def _init_db(self):
        """Initializes SQLite database tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bee_crossing_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        date_str TEXT NOT NULL,
                        bee_id INTEGER NOT NULL,
                        direction TEXT NOT NULL,
                        duration REAL NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_summary (
                        date_str TEXT PRIMARY KEY,
                        total_in INTEGER DEFAULT 0,
                        total_out INTEGER DEFAULT 0,
                        last_updated TEXT
                    )
                """)
                conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite DB: {e}")

    def _init_csv(self):
        """Initializes CSV header if file doesn't exist."""
        if not os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Date", "Bee_ID", "Direction", "Duration_Sec"])
                logger.info(f"CSV log initialized at {self.csv_path}")
            except Exception as e:
                logger.error(f"Failed to initialize CSV log: {e}")

    def log_event(self, bee_id: int, direction: str, duration: float = 0.0):
        """Logs a single IN/OUT crossing event."""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        date_str = now.strftime("%Y-%m-%d")

        # 1. Insert into SQLite
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO bee_crossing_events (timestamp, date_str, bee_id, direction, duration)
                    VALUES (?, ?, ?, ?, ?)
                """, (timestamp, date_str, bee_id, direction, round(duration, 2)))

                # Update daily summary
                if direction == "IN":
                    cursor.execute("""
                        INSERT INTO daily_summary (date_str, total_in, total_out, last_updated)
                        VALUES (?, 1, 0, ?)
                        ON CONFLICT(date_str) DO UPDATE SET
                            total_in = total_in + 1,
                            last_updated = ?
                    """, (date_str, timestamp, timestamp))
                elif direction == "OUT":
                    cursor.execute("""
                        INSERT INTO daily_summary (date_str, total_in, total_out, last_updated)
                        VALUES (?, 0, 1, ?)
                        ON CONFLICT(date_str) DO UPDATE SET
                            total_out = total_out + 1,
                            last_updated = ?
                    """, (date_str, timestamp, timestamp))

                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log event to SQLite: {e}")

        # 2. Append to CSV
        try:
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, date_str, bee_id, direction, round(duration, 2)])
        except Exception as e:
            logger.error(f"Failed to append event to CSV: {e}")

        return {
            "timestamp": timestamp,
            "date_str": date_str,
            "bee_id": bee_id,
            "direction": direction,
            "duration": round(duration, 2)
        }

    def get_today_counts(self):
        """Returns (total_in, total_out, net_count) for today."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT total_in, total_out FROM daily_summary WHERE date_str = ?
                """, (date_str,))
                row = cursor.fetchone()
                if row:
                    total_in, total_out = row
                    return total_in, total_out, (total_in - total_out)
        except Exception as e:
            logger.error(f"Failed to fetch today's count: {e}")

        return 0, 0, 0

    def get_recent_events(self, limit: int = 50):
        """Returns the most recent N crossing events for UI display."""
        events = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp, bee_id, direction, duration
                    FROM bee_crossing_events
                    ORDER BY id DESC LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                for r in rows:
                    events.append({
                        "timestamp": r[0],
                        "bee_id": r[1],
                        "direction": r[2],
                        "duration": r[3]
                    })
        except Exception as e:
            logger.error(f"Failed to fetch recent events: {e}")
        return events

    def reset_today_counts(self):
        """Resets today's counter in database."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO daily_summary (date_str, total_in, total_out, last_updated)
                    VALUES (?, 0, 0, ?)
                    ON CONFLICT(date_str) DO UPDATE SET
                        total_in = 0,
                        total_out = 0,
                        last_updated = ?
                """, (date_str, now_str, now_str))
                conn.commit()
            logger.info("Today's counts reset.")
        except Exception as e:
            logger.error(f"Failed to reset today's counts: {e}")

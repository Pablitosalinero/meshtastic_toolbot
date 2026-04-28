import sqlite3
import time

class Database:
    def __init__(self, db_path="toolbot.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Table for logging telemetry
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS telemetry_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    from_node INTEGER,
                    channel TEXT,
                    rssi REAL,
                    snr REAL,
                    hop_start INTEGER,
                    hop_limit INTEGER,
                    relay_node INTEGER,
                    text TEXT
                )
            ''')
            
            # Table for cooldown tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cooldowns (
                    node_id INTEGER PRIMARY KEY,
                    last_request_time REAL
                )
            ''')
            conn.commit()

    def check_and_update_cooldown(self, node_id, cooldown_seconds):
        """
        Returns True if the node is allowed to execute a command.
        Returns False if the node is still in cooldown.
        Updates the cooldown timer if allowed.
        """
        current_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_request_time FROM cooldowns WHERE node_id = ?", (node_id,))
            row = cursor.fetchone()
            
            if row:
                last_time = row[0]
                if current_time - last_time < cooldown_seconds:
                    return False
                    
            # Allowed, update or insert time
            cursor.execute('''
                INSERT INTO cooldowns (node_id, last_request_time) 
                VALUES (?, ?) 
                ON CONFLICT(node_id) 
                DO UPDATE SET last_request_time = ?
            ''', (node_id, current_time, current_time))
            conn.commit()
            return True

    def log_telemetry(self, from_node, channel, rssi, snr, hop_start, hop_limit, relay_node, text):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO telemetry_logs (timestamp, from_node, channel, rssi, snr, hop_start, hop_limit, relay_node, text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (time.time(), from_node, channel, rssi, snr, hop_start, hop_limit, relay_node, text))
            conn.commit()

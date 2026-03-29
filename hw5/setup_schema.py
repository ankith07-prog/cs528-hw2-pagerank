import os
import pymysql

DB_HOST = os.environ.get("DB_HOST", "")
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "hw5db")


def main():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        autocommit=True
    )

    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            cur.execute(f"USE {DB_NAME}")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS request_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    country VARCHAR(100),
                    client_ip VARCHAR(100),
                    gender VARCHAR(50),
                    age INT NULL,
                    income VARCHAR(100),
                    is_banned BOOLEAN,
                    time_of_day VARCHAR(50),
                    requested_file VARCHAR(255)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    requested_file VARCHAR(255),
                    error_code INT
                )
            """)

        print("Schema setup complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

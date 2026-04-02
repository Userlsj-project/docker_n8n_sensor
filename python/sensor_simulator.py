import os
import time
import random
import psycopg2
from datetime import datetime

DB_CONFIG = {
    "host":     os.environ.get("POSTGRES_HOST", "postgresql"),
    "port":     int(os.environ.get("POSTGRES_PORT", 5432)),
    "dbname":   os.environ.get("POSTGRES_DB", "sensordb"),
    "user":     os.environ.get("POSTGRES_USER", "sensor_user"),
    "password": os.environ.get("POSTGRES_PASSWORD", "sensor_pass"),
}

MAX_RETRIES = 10
RETRY_INTERVAL = 3   # seconds
INSERT_INTERVAL = 5  # seconds


def connect_with_retry():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            print(f"[{datetime.now()}] PostgreSQL 연결 성공", flush=True)
            return conn
        except psycopg2.OperationalError as e:
            print(f"[{datetime.now()}] 연결 실패 ({attempt}/{MAX_RETRIES}): {e}", flush=True)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_INTERVAL)
    raise RuntimeError("PostgreSQL 연결에 실패했습니다. (최대 재시도 초과)")


def main():
    conn = connect_with_retry()
    conn.autocommit = True
    cursor = conn.cursor()

    print(f"[{datetime.now()}] 센서 데이터 시뮬레이션 시작 (5초 간격)", flush=True)

    while True:
        temperature = round(random.uniform(15.0, 35.0), 2)
        humidity    = round(random.uniform(30.0, 90.0), 2)
        pressure    = round(random.uniform(980.0, 1025.0), 2)

        try:
            cursor.execute(
                "INSERT INTO sensor_data (temperature, humidity, pressure) VALUES (%s, %s, %s)",
                (temperature, humidity, pressure),
            )
            print(
                f"[{datetime.now()}] INSERT OK — "
                f"온도: {temperature}°C  습도: {humidity}%  기압: {pressure}hPa",
                flush=True,
            )
        except psycopg2.Error as e:
            print(f"[{datetime.now()}] INSERT 오류: {e}", flush=True)
            # 연결 재시도
            try:
                conn.close()
            except Exception:
                pass
            conn = connect_with_retry()
            conn.autocommit = True
            cursor = conn.cursor()

        time.sleep(INSERT_INTERVAL)


if __name__ == "__main__":
    main()

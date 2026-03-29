from flask import Flask, Response, request
from google.cloud import storage
import logging
import requests
import os
import time
from datetime import datetime
import pymysql

app = Flask(__name__)

BUCKET_NAME = "hw-2-486907-ankith07-pagerank-001"
storage_client = storage.Client()

FORBIDDEN_COUNTRIES = [
    "North Korea", "Iran", "Cuba", "Myanmar",
    "Iraq", "Libya", "Sudan", "Zimbabwe", "Syria"
]

DB_HOST = os.environ.get("DB_HOST", "")
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "hw5db")
ALERT_SERVICE_URL = os.environ.get("ALERT_SERVICE_URL", "http://10.128.0.4:5001/alert")


def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=True
    )


def get_time_of_day():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 21:
        return "evening"
    return "night"


def extract_request_info(req, filename):
    start = time.perf_counter()

    country = req.headers.get("X-country", "Unknown")
    client_ip = (
        req.headers.get("X-client-IP")
        or req.headers.get("X-client-ip")
        or req.headers.get("X-forwarded-for")
        or req.remote_addr
        or "Unknown"
    )
    gender = req.headers.get("X-gender", "Unknown")
    income = req.headers.get("X-income", "Unknown")

    age_raw = req.headers.get("X-age")
    try:
        age = int(age_raw) if age_raw is not None else None
    except ValueError:
        age = None

    is_banned = country in FORBIDDEN_COUNTRIES
    time_of_day = get_time_of_day()

    elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "country": country,
        "client_ip": client_ip,
        "gender": gender,
        "age": age,
        "income": income,
        "is_banned": is_banned,
        "time_of_day": time_of_day,
        "requested_file": filename,
        "header_time_ms": elapsed_ms
    }


def read_file_from_gcs(filename):
    start = time.perf_counter()

    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob("pages/" + filename)

    if blob.exists():
        data = blob.download_as_text()
        elapsed_ms = (time.perf_counter() - start) * 1000
        return True, data, elapsed_ms

    elapsed_ms = (time.perf_counter() - start) * 1000
    return False, None, elapsed_ms


def insert_request_log(info):
    start = time.perf_counter()

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO request_logs
                (country, client_ip, gender, age, income, is_banned, time_of_day, requested_file)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    info["country"],
                    info["client_ip"],
                    info["gender"],
                    info["age"],
                    info["income"],
                    info["is_banned"],
                    info["time_of_day"],
                    info["requested_file"]
                )
            )
    finally:
        conn.close()

    return (time.perf_counter() - start) * 1000


def insert_error_log(filename, error_code):
    start = time.perf_counter()

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO error_logs
                (requested_file, error_code)
                VALUES (%s, %s)
                """,
                (filename, error_code)
            )
    finally:
        conn.close()

    return (time.perf_counter() - start) * 1000


def make_timed_response(body, status_code, mimetype="text/plain"):
    start = time.perf_counter()
    response = Response(body, status=status_code, mimetype=mimetype)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return response, elapsed_ms


@app.route('/<path:filename>', methods=['GET'])
def get_file(filename):
    info = extract_request_info(request, filename)

    try:
        request_log_time_ms = insert_request_log(info)
    except Exception as e:
        logging.exception(f"Request log insert failed: {e}")
        request_log_time_ms = -1

    if info["is_banned"]:
        logging.critical(f"Forbidden request from {info['country']}")

        try:
            requests.post(
                ALERT_SERVICE_URL,
                json={"country": info["country"]},
                timeout=5
            )
        except Exception as e:
            logging.exception(f"Alert forwarding failed: {e}")

        try:
            error_log_time_ms = insert_error_log(filename, 403)
        except Exception as e:
            logging.exception(f"Error log insert failed: {e}")
            error_log_time_ms = -1

        response, response_time_ms = make_timed_response("Forbidden", 403)

        logging.info(
            f"header_time_ms={info['header_time_ms']:.3f}, "
            f"gcs_read_time_ms=0.000, "
            f"request_log_time_ms={request_log_time_ms:.3f}, "
            f"error_log_time_ms={error_log_time_ms:.3f}, "
            f"response_time_ms={response_time_ms:.3f}"
        )

        return response

    file_found, data, gcs_read_time_ms = read_file_from_gcs(filename)

    if file_found:
        response, response_time_ms = make_timed_response(data, 200)

        logging.info(
            f"header_time_ms={info['header_time_ms']:.3f}, "
            f"gcs_read_time_ms={gcs_read_time_ms:.3f}, "
            f"request_log_time_ms={request_log_time_ms:.3f}, "
            f"error_log_time_ms=0.000, "
            f"response_time_ms={response_time_ms:.3f}"
        )

        return response

    logging.warning("404 request")

    try:
        error_log_time_ms = insert_error_log(filename, 404)
    except Exception as e:
        logging.exception(f"Error log insert failed: {e}")
        error_log_time_ms = -1

    response, response_time_ms = make_timed_response("File not found", 404)

    logging.info(
        f"header_time_ms={info['header_time_ms']:.3f}, "
        f"gcs_read_time_ms={gcs_read_time_ms:.3f}, "
        f"request_log_time_ms={request_log_time_ms:.3f}, "
        f"error_log_time_ms={error_log_time_ms:.3f}, "
        f"response_time_ms={response_time_ms:.3f}"
    )

    return response


@app.errorhandler(405)
def method_not_allowed(e):
    filename = request.path.lstrip("/") or "UNKNOWN"
    info = extract_request_info(request, filename)

    try:
        request_log_time_ms = insert_request_log(info)
    except Exception as ex:
        logging.exception(f"Request log insert failed: {ex}")
        request_log_time_ms = -1

    logging.warning("501 method not implemented")

    try:
        error_log_time_ms = insert_error_log(filename, 501)
    except Exception as ex:
        logging.exception(f"Error log insert failed: {ex}")
        error_log_time_ms = -1

    response, response_time_ms = make_timed_response("Not implemented", 501)

    logging.info(
        f"header_time_ms={info['header_time_ms']:.3f}, "
        f"gcs_read_time_ms=0.000, "
        f"request_log_time_ms={request_log_time_ms:.3f}, "
        f"error_log_time_ms={error_log_time_ms:.3f}, "
        f"response_time_ms={response_time_ms:.3f}"
    )

    return response


app.run(host="0.0.0.0", port=8080)

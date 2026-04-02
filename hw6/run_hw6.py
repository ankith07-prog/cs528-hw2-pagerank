import os
from pathlib import Path

import pandas as pd
import pymysql
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from google.cloud import storage


DB_HOST = os.environ["DB_HOST"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_NAME = os.environ["DB_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "hw-2-486907")

ROOT = Path(__file__).resolve().parent
SCHEMA_SQL = ROOT / "schema_3nf.sql"
MIGRATE_SQL = ROOT / "migrate_to_3nf.sql"


def get_conn():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=30,
        read_timeout=60,
        write_timeout=60,
    )


def run_sql_file(conn, path: Path):
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()

    statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
    with conn.cursor() as cur:
        for stmt in statements:
            cur.execute(stmt)


def load_model1_data(conn):
    query = """
    SELECT
        m.client_ip,
        c.country_name AS country
    FROM ip_country_map m
    JOIN countries c
      ON m.country_id = c.country_id
    WHERE m.client_ip IS NOT NULL
      AND c.country_name IS NOT NULL
      AND c.country_name <> 'Unknown'
    """
    return pd.read_sql(query, conn)


def load_model2_data(conn):
    query = """
    SELECT
        r.request_id,
        r.client_ip,
        c.country_name AS country,
        c.is_banned,
        r.gender,
        r.age,
        r.income,
        r.time_of_day,
        r.requested_file
    FROM requests_3nf r
    JOIN ip_country_map m
      ON r.client_ip = m.client_ip
    JOIN countries c
      ON m.country_id = c.country_id
    WHERE r.income IS NOT NULL
      AND r.income <> 'Unknown'
    """
    return pd.read_sql(query, conn)


def upload_to_bucket(local_path: str, object_name: str):
    client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(object_name)
    blob.upload_from_filename(local_path)
    print(f"Uploaded to gs://{BUCKET_NAME}/{object_name}")


def run_model1(df: pd.DataFrame):
    train_df, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["country"],
    )

    ip_to_country = dict(zip(train_df["client_ip"], train_df["country"]))
    y_true = test_df["country"].tolist()
    y_pred = [ip_to_country.get(ip, "UNKNOWN") for ip in test_df["client_ip"]]

    full_map = dict(zip(df["client_ip"], df["country"]))
    y_pred = [
        pred if pred != "UNKNOWN" else full_map.get(ip, "UNKNOWN")
        for pred, ip in zip(y_pred, test_df["client_ip"])
    ]

    acc = accuracy_score(y_true, y_pred)

    out = test_df.copy()
    out["predicted_country"] = y_pred
    out["correct"] = out["country"] == out["predicted_country"]
    return acc, out


def run_model2(df: pd.DataFrame):
    data = df.copy()

    # Clean string columns
    for col in ["country", "gender", "income", "time_of_day", "requested_file"]:
        data[col] = data[col].astype(str).str.strip()

    # Normalize target values
    data["income"] = data["income"].str.title()

    # Keep only expected labels
    valid_income = {"High", "Medium", "Low"}
    data = data[data["income"].isin(valid_income)].copy()

    def age_bucket(val):
        if pd.isna(val):
            return "Unknown"
        try:
            val = int(val)
        except Exception:
            return "Unknown"

        if val < 18:
            return "<18"
        if val <= 25:
            return "18-25"
        if val <= 40:
            return "26-40"
        if val <= 60:
            return "41-60"
        return "60+"

    data["age_bucket"] = data["age"].apply(age_bucket)

    features = [
        "country",
        "is_banned",
        "gender",
        "age_bucket",
        "time_of_day",
        "requested_file",
    ]
    target = "income"

    data = data[features + [target]].dropna().copy()

    print("\nModel 2 target distribution:")
    print(data[target].value_counts())

    if data[target].nunique() < 2:
        raise ValueError(
            f"Model 2 target has fewer than 2 classes after cleaning: {data[target].unique()}"
        )

    X = data[features]
    y = data[target]

    train_X, test_X, train_y, test_y = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    categorical_features = features

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
        ]
    )

    model = Pipeline(
        steps=[
            ("prep", preprocessor),
            ("clf", RandomForestClassifier(
                n_estimators=200,
                max_depth=12,
                min_samples_leaf=3,
                random_state=42,
                n_jobs=-1,
            ))
        ]
    )

    model.fit(train_X, train_y)
    pred_y = model.predict(test_X)

    acc = accuracy_score(test_y, pred_y)
    report = classification_report(
        test_y,
        pred_y,
        labels=["High", "Medium", "Low"],
        zero_division=0
    )

    out = test_X.copy()
    out["actual_income"] = test_y.values
    out["predicted_income"] = pred_y
    out["correct"] = out["actual_income"] == out["predicted_income"]

    return acc, out, report


def main():
    conn = get_conn()

    try:
        print("Applying 3NF schema...")
        run_sql_file(conn, SCHEMA_SQL)

        print("Migrating data...")
        run_sql_file(conn, MIGRATE_SQL)

        print("Loading model 1 data...")
        model1_df = load_model1_data(conn)
        print(f"Model 1 rows: {len(model1_df)}")

        print("Loading model 2 data...")
        model2_df = load_model2_data(conn)
        print(f"Model 2 rows: {len(model2_df)}")

        acc1, out1 = run_model1(model1_df)
        print(f"Model 1 accuracy: {acc1:.4f}")

        acc2, out2, report2 = run_model2(model2_df)
        print(f"Model 2 accuracy: {acc2:.4f}")
        print(report2)

        output_dir = Path("/root/hw6_outputs")
        output_dir.mkdir(parents=True, exist_ok=True)

        m1_csv = str(output_dir / "model1_ip_to_country_test_output.csv")
        m2_csv = str(output_dir / "model2_income_test_output.csv")
        summary_txt = str(output_dir / "hw6_summary.txt")

        out1.to_csv(m1_csv, index=False)
        out2.to_csv(m2_csv, index=False)

        with open(summary_txt, "w", encoding="utf-8") as f:
            f.write("HW6 MODEL SUMMARY\n")
            f.write("=================\n")
            f.write(f"Model 1 accuracy (client_ip -> country): {acc1:.4f}\n")
            f.write(f"Model 2 accuracy (predict income): {acc2:.4f}\n\n")
            f.write("Income model classification report:\n")
            f.write(report2)
            f.write("\n")

        print(f"Saved local outputs to {output_dir}")

        try:
            upload_to_bucket(m1_csv, "hw6/model1_ip_to_country_test_output.csv")
            upload_to_bucket(m2_csv, "hw6/model2_income_test_output.csv")
            upload_to_bucket(summary_txt, "hw6/hw6_summary.txt")
        except Exception as e:
            print(f"Bucket upload failed: {e}")
            print(f"Local files are still available in {output_dir}")

        print("Done.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

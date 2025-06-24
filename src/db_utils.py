
import psycopg2
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "akinator_assets"),
    "user": os.getenv("DB_USER", "akinator_user"),
    "password": os.getenv("DB_PASSWORD", "your_password"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", 5432)
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def insert_ticker_if_not_exists(ticker):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO tickers (ticker) VALUES (%s) ON CONFLICT (ticker) DO NOTHING;",
            (ticker,)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

def insert_agent_output(ticker, agent_output, model_used='bedrock'):
    insert_ticker_if_not_exists(ticker)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM tickers WHERE ticker = %s;", (ticker,))
        ticker_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO agent_outputs (
                ticker_id, raw_output, duration, search_calls, timestamp,
                executive_summary, bull_case, bear_case, investment_takeaway,
                analytical_reasoning, search_summary, model_used, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                ticker_id,
                json.dumps(agent_output),
                agent_output.get("duration"),
                agent_output.get("search_calls"),
                datetime.fromisoformat(agent_output.get("timestamp")),
                agent_output.get("executive_summary"),
                agent_output.get("bull_case"),
                agent_output.get("bear_case"),
                agent_output.get("investment_takeaway"),
                agent_output.get("analytical_reasoning"),
                agent_output.get("search_summary"),
                model_used,
                datetime.now()
            )
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

def fetch_latest_agent_output(ticker):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM tickers WHERE ticker = %s;", (ticker,))
        result = cur.fetchone()
        if not result:
            return None
        ticker_id = result[0]

        cur.execute(
            "SELECT raw_output FROM agent_outputs WHERE ticker_id = %s ORDER BY timestamp DESC LIMIT 1;",
            (ticker_id,)
        )
        row = cur.fetchone()
        return json.loads(row[0]) if row else None
    finally:
        cur.close()
        conn.close()


def insert_moat_analysis(ticker, sections, duration, model_used="bedrock"):
    insert_ticker_if_not_exists(ticker)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM tickers WHERE ticker = %s;", (ticker,))
        ticker_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO moat_analysis (
                ticker_id, duration, analysis, model_used, generated_at
            )
            VALUES (%s, %s, %s, %s, %s);
            """,
            (
                ticker_id,
                duration,
                json.dumps(sections),
                model_used,
                datetime.now()
            )
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

def fetch_latest_moat_analysis(ticker):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM tickers WHERE ticker = %s;", (ticker,))
        result = cur.fetchone()
        if not result:
            return None
        ticker_id = result[0]

        cur.execute(
            """
            SELECT analysis, duration
            FROM moat_analysis
            WHERE ticker_id = %s
            ORDER BY generated_at DESC
            LIMIT 1;
            """,
            (ticker_id,)
        )
        row = cur.fetchone()
        return {"sections": json.loads(row[0]), "duration": row[1]} if row else None
    finally:
        cur.close()
        conn.close()
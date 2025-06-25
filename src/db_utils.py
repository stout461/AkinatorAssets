
import psycopg2
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "akinator_assets"),
    "user": os.getenv("DB_USER", "akinator_user"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", 5432)
}

def get_connection():
    print("🧪 Connecting with:")
    print("  DB_USER =", DB_CONFIG["user"])
    print("  DB_PASSWORD =", DB_CONFIG["password"])
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

        sections = agent_output.get("sections", {})

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
                datetime.fromisoformat(str(agent_output.get("timestamp"))) if agent_output.get("timestamp") else datetime.now(),
                agent_output.get("executive_summary"),
                sections.get("bull_case"),
                sections.get("bear_case"),
                sections.get("investment_takeaway"),
                sections.get("analytical_reasoning"),
                sections.get("search_summary"),
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
            "SELECT raw_output, timestamp FROM agent_outputs WHERE ticker_id = %s ORDER BY timestamp DESC LIMIT 1;",
            (ticker_id,)
        )
        row = cur.fetchone()
        if row:
            raw_output, timestamp = row
            if timestamp and timestamp >= datetime.now() - timedelta(days=7):
                return raw_output
            else:
                print(f"⚠️ Cached stock analysis for {ticker} is older than 7 days.")
        return None
    finally:
        cur.close()
        conn.close()


def insert_moat_analysis(ticker, sections, duration, model_used="bedrock"):
    insert_ticker_if_not_exists(ticker)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM tickers WHERE ticker = %s;", (ticker,))
        result = cur.fetchone()
        if not result:
            print(f"❌ Could not find ticker_id for {ticker}")
            return
        ticker_id = result[0]

        print(f"📥 Inserting MOAT analysis for {ticker} (ID {ticker_id})...")

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
        print(f"✅ MOAT analysis inserted for {ticker}")

    except Exception as e:
        print(f"❌ Failed to insert moat analysis for {ticker}: {e}")
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
            "SELECT analysis, duration, generated_at FROM moat_analysis WHERE ticker_id = %s ORDER BY generated_at DESC LIMIT 1;",
            (ticker_id,)
        )
        row = cur.fetchone()
        if row:
            analysis, duration, generated_at = row
            if generated_at and generated_at >= datetime.now() - timedelta(days=7):
                return {"sections": analysis, "duration": duration}
            else:
                print(f"⚠️ Cached moat analysis for {ticker} is older than 7 days.")
        return None
    finally:
        cur.close()
        conn.close()
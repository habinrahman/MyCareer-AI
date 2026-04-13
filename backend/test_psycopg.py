import psycopg

DATABASE_URL = (
    "postgresql://postgres.egovsdkluhxqibclaqsq:"
    "Hamdiya123%40@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres"
)

try:
    print("🔄 Attempting to connect to Supabase...")

    conn = psycopg.connect(
        DATABASE_URL,
        sslmode="require"
    )

    print("✅ Connected successfully!")
    conn.close()

except Exception as e:
    print("❌ Connection failed:")
    print(e)
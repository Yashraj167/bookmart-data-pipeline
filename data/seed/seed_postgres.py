
import os
import random

import psycopg2
from psycopg2.extras import execute_batch
from faker import Faker
from dotenv import load_dotenv


# Load environment variables from the project root .env file
load_dotenv(dotenv_path=".env")

fake = Faker()


def main():
    # Read the Neon PostgreSQL connection string
    database_url = os.environ.get("NEON_DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "NEON_DATABASE_URL not found. "
            "Check that your .env file exists in the project root."
        )

    conn = None

    try:
        # Connect to Neon PostgreSQL
        conn = psycopg2.connect(
            database_url,
            connect_timeout=20,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
        )

        print("Connected to Neon PostgreSQL successfully.")

        with conn.cursor() as cur:

            # 1. Create tables if they do not exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id SERIAL PRIMARY KEY,
                    full_name TEXT,
                    email TEXT,
                    country TEXT,
                    created_at TIMESTAMP DEFAULT now(),
                    updated_at TIMESTAMP DEFAULT now()
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id SERIAL PRIMARY KEY,
                    customer_id INT REFERENCES customers(customer_id),
                    status TEXT,
                    currency TEXT,
                    total_amount NUMERIC(10, 2),
                    created_at TIMESTAMP DEFAULT now(),
                    updated_at TIMESTAMP DEFAULT now()
                );
            """)

            print("Tables created or already exist.")

            # 2. Check whether data has already been seeded
            cur.execute("SELECT COUNT(*) FROM customers")
            customer_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM orders")
            order_count = cur.fetchone()[0]

            if customer_count > 0 or order_count > 0:
                print(
                    f"Existing data found: {customer_count} customers, "
                    f"{order_count} orders."
                )
                print(
                    "Seeding skipped to avoid duplicates. "
                    "Review the counts before deciding whether to resume."
                )

                # Commit table creation if needed, without inserting duplicates
                conn.commit()
                return

            # 3. Generate 500 customer records
            print("Preparing 500 customers...")

            customers = [
                (fake.name(), fake.unique.email(), fake.country_code())
                for _ in range(500)
            ]

            # 4. Insert customers in batches
            print("Inserting customers...")

            execute_batch(
                cur,
                """
                INSERT INTO customers (full_name, email, country)
                VALUES (%s, %s, %s)
                """,
                customers,
                page_size=100,
            )

            # 5. Retrieve generated customer IDs
            cur.execute("SELECT customer_id FROM customers")
            customer_ids = [row[0] for row in cur.fetchall()]

            if not customer_ids:
                raise RuntimeError(
                    "No customer IDs found; cannot create orders."
                )

            # 6. Generate 2,000 order records
            print("Preparing 2,000 orders...")

            orders = [
                (
                    random.choice(customer_ids),
                    random.choice(
                        ["placed", "shipped", "delivered", "cancelled"]
                    ),
                    random.choice(["USD", "EUR", "GBP", "INR"]),
                    round(random.uniform(8, 250), 2),
                )
                for _ in range(2000)
            ]

            # 7. Insert orders in batches
            print("Inserting orders...")

            execute_batch(
                cur,
                """
                INSERT INTO orders (
                    customer_id,
                    status,
                    currency,
                    total_amount,
                    created_at,
                    updated_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    now() - (random() * interval '90 days'),
                    now()
                )
                """,
                orders,
                page_size=200,
            )

        # 8. Commit only after both sets of inserts succeed
        conn.commit()

        print("\nSeed completed successfully!")
        print("Customers inserted: 500")
        print("Orders inserted: 2000")

    except Exception as error:
        if conn is not None:
            conn.rollback()

        print("\nSeed failed. Transaction rolled back.")
        print("Error type:", type(error).__name__)
        print("Error details:", str(error))
        raise

    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")


if __name__ == "__main__":
    main()

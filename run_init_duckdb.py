import duckdb
import time

def run_analysis():
    # Connect to a DuckDB database file
    con = duckdb.connect('financial_analysis.db')
    
    print("--- [1] Initializing Schema and Loading Data ---")
    with open('init_duckdb.sql', 'r') as f:
        sql_script = f.read()
    
    start_time = time.time()
    try:
        # Execute the script
        con.execute(sql_script)
        print(f"Data Loaded successfully in {time.time() - start_time:.4f} seconds.")

        # Add benchmark query (e.g., finding the top 5 countries by transaction volume)
        print("\n--- [2] Analytical Benchmark: Top 5 Countries by Total TX Volume ---")
        benchmark_query = """
            SELECT u.country, SUM(t.amount) as total_vol
            FROM transactions t
            JOIN accounts a ON t.src_account_id = a.account_id
            JOIN users u ON a.user_id = u.user_id
            GROUP BY u.country
            ORDER BY total_vol DESC
            LIMIT 5;
        """
        start_query = time.time()
        results = con.execute(benchmark_query).fetchall()
        print(f"Analysis complete in {time.time() - start_query:.4f} seconds.")
        for row in results:
            print(f"  {row[0]}: ${row[1]:,.2f}")

        # Summary Statistics
        print("\n--- [3] Data Summary ---")
        summary = con.execute("""
            SELECT 'Total Users' as stat, count(*) FROM users
            UNION ALL SELECT 'Total Accounts', count(*) FROM accounts
            UNION ALL SELECT 'Total Transactions', count(*) FROM transactions;
        """).fetchall()
        for s in summary:
            print(f"  {s[0]}: {s[1]}")

    except Exception as e:
        print(f"Error executing script: {e}")
    finally:
        con.close()

if __name__ == "__main__":
    run_analysis()

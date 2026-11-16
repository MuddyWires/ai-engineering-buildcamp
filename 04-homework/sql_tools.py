import os
import urllib.request

import duckdb

DATA_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
HERE = os.path.dirname(os.path.abspath(__file__))
PARQUET_FILE = os.path.join(HERE, "yellow_tripdata_2024-01.parquet")

con = duckdb.connect(os.path.join(HERE, "taxi.db"))


def setup_database():
    """Download the parquet file and load it into DuckDB."""
    if not os.path.exists(PARQUET_FILE):
        print(f"Downloading {DATA_URL}...")
        urllib.request.urlretrieve(DATA_URL, PARQUET_FILE)

    con.execute(f"""
        CREATE TABLE IF NOT EXISTS trips AS
        SELECT * FROM '{PARQUET_FILE}'
    """)
    count = con.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    print(f"Loaded {count} rows")
    return count

class SQLTools:
    """
    Provides schema inspection and SQL query execution over the taxi trips table.
    """

    def __init__(self, connection: duckdb.DuckDBPyConnection = con) -> None:
        """
        Initialize the SQLTools instance.

        Args:
            connection: DuckDB connection holding the `trips` table.
        """
        self.connection = connection

    def get_schema(self) -> str:
        """
        Get the column names and types of the trips table.

        Returns:
            str: One "column_name: column_type" line per column.
        """
        rows = self.connection.execute("DESCRIBE trips").fetchall()
        return "\n".join(f"{row[0]}: {row[1]}" for row in rows)

    def run_sql(self, query: str) -> str:
        """
        Execute a SQL query and return the results as text.

        Args:
            query (str): The SQL query to execute.

        Returns:
            str: Column headers followed by up to 50 data rows, or an error message.
        """
        try:
            result = self.connection.execute(query)
            columns = [col[0] for col in result.description]
            rows = result.fetchmany(50)
        except Exception as e:
            return f"Error: {e}"

        lines = [" | ".join(columns)]
        lines.extend(" | ".join(str(value) for value in row) for row in rows)
        return "\n".join(lines)

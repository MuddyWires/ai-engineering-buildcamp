import os
from datetime import datetime, timedelta, timezone

import dotenv
from logfire.query_client import LogfireQueryClient

dotenv.load_dotenv()

client = LogfireQueryClient(read_token=os.environ["LOGFIRE_READ_TOKEN"])

# One row per root span; the grouped session is the 'trivia_session' root.
sql = """
SELECT trace_id, span_name, start_timestamp, duration
FROM records
WHERE parent_span_id IS NULL
ORDER BY start_timestamp DESC
LIMIT 20
"""

result = client.query_json_rows(
    sql, min_timestamp=datetime.now(timezone.utc) - timedelta(days=7)
)
for row in result["rows"]:
    marker = "  <-- grouped session" if row["span_name"] == "trivia_session" else ""
    print(row["trace_id"], row["span_name"], row["start_timestamp"], marker)

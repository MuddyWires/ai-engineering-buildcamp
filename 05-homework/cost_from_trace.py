import os
from datetime import datetime, timedelta, timezone

import dotenv
from logfire.query_client import LogfireQueryClient

dotenv.load_dotenv()
TRACE_ID = "01a1eec28030fdbd95dadc22821b0d33"
client = LogfireQueryClient(read_token=os.environ["LOGFIRE_READ_TOKEN"])

sql = f"""
SELECT span_name,
       attributes->>'gen_ai.aggregated_usage.input_tokens' AS inp,
       attributes->>'gen_ai.aggregated_usage.output_tokens' AS outp
FROM records
WHERE trace_id = '{TRACE_ID}'
  AND (span_name = 'agent run' OR span_name LIKE 'invoke_agent%')
"""
rows = client.query_json_rows(
    sql, min_timestamp=datetime.now(timezone.utc) - timedelta(days=14)
)["rows"]

inp = sum(int(r["inp"] or 0) for r in rows)
out = sum(int(r["outp"] or 0) for r in rows)

MODEL_PRICES = {"gpt-4o-mini": {"input": 0.15, "output": 0.60}}


def calculate_cost(model_name, input_tokens, output_tokens):
    prices = MODEL_PRICES[model_name.lower()]
    return (input_tokens / 1_000_000) * prices["input"] + (
        output_tokens / 1_000_000
    ) * prices["output"]


print(f"agent spans={len(rows)} input={inp} output={out}")
print(f"cost=${calculate_cost('gpt-4o-mini', inp, out):.6f}")

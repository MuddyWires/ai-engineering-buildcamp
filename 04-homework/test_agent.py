import pytest

from sql_agent import SQLResult, create_agent
from sql_tools import SQLTools, setup_database
import utils
from judge import assert_criteria
import re

@pytest.mark.asyncio
async def test_trips_more_than_5_passengers():
    setup_database()
    expected_count=SQLTools().connection.execute("SELECT COUNT(*) FROM trips WHERE passenger_count>5").fetchone()[0]
    agent=create_agent()
    result=await agent.run(
        user_prompt="How many trips had more than 5 passengers?",
        output_type=SQLResult
    )
    output=result.output
    print(f"expected_count={expected_count}")
    print(output.result_text)
    assert isinstance(output.sql_query,str)
    assert output.sql_query.strip()!= ""
    assert str(expected_count) in output.result_text.replace(",", "")


@pytest.mark.asyncio
async def test_what_is_the_most_common_payment_type():
    setup_database()
    agent=create_agent()
    result=await agent.run(
            user_prompt="What is the most common payment type?",
            output_type=SQLResult
        )
    output = result.output
    messages=result.new_messages()
    tools=utils.collect_tools(messages)
    print(tools)

    assert tools[0].name == "get_schema"
    assert any(x.name == "run_sql" for x in tools)

    payment_type, trip_count = SQLTools().connection.execute(
        "SELECT payment_type, COUNT(*) AS cnt FROM trips "
        "GROUP BY payment_type ORDER BY cnt DESC LIMIT 1"
    ).fetchone()

    assert str(trip_count) in output.result_text.replace(",", "")
    assert re.search(rf"\b{payment_type}\b", output.result_text)

    print(f"expected: payment_type={payment_type}, trip_count={trip_count}")
    print(f"agent said: {output.result_text}")


@pytest.mark.asyncio
async def test_hour_with_highest_average_fare():
    setup_database()
    agent = create_agent()
    result = await agent.run(
        user_prompt="Which hour of the day has the highest average fare amount?",
        output_type=SQLResult,
    )
    print(result.output.result_text)

    await assert_criteria(result, [
        "the SQL query correctly calculates average fare by hour of day",
        "the result identifies a specific hour as having the highest average fare",
        "the result includes the actual average fare amount",
    ])


# ---------- helpers ----------

def numbers_in(text):
    """All numbers in the text, with thousands separators removed."""
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))]


def contains_number(text, expected, tol=0.01):
    return any(abs(n - expected) <= tol for n in numbers_in(text))


async def ask(question):
    setup_database()
    result = await create_agent().run(user_prompt=question, output_type=SQLResult)
    tools = utils.collect_tools(result.new_messages())
    print(f"\nQ: {question}\nSQL: {result.output.sql_query}\nA: {result.output.result_text}")
    return result.output, tools


def scalar(sql):
    return SQLTools().connection.execute(sql).fetchone()


def check_tool_order(tools):
    assert tools[0].name == "get_schema"
    assert any(t.name == "run_sql" for t in tools)


# ---------- more questions ----------

@pytest.mark.asyncio
async def test_average_tip_for_credit_card():
    output, tools = await ask("What is the average tip amount for credit card payments?")
    expected = scalar("SELECT AVG(tip_amount) FROM trips WHERE payment_type = 1")[0]
    check_tool_order(tools)
    sql = output.sql_query.lower()
    assert "tip_amount" in sql and "payment_type" in sql
    assert contains_number(output.result_text, expected, tol=0.01), f"expected ~{expected:.4f}"


@pytest.mark.asyncio
async def test_pickup_location_with_most_trips():
    output, tools = await ask("Which pickup location (PULocationID) has the most trips?")
    loc, cnt = scalar(
        "SELECT PULocationID, COUNT(*) c FROM trips GROUP BY PULocationID ORDER BY c DESC LIMIT 1"
    )
    check_tool_order(tools)
    assert "pulocationid" in output.sql_query.lower()
    assert contains_number(output.result_text, loc, tol=0)
    assert contains_number(output.result_text, cnt, tol=0)


@pytest.mark.asyncio
async def test_average_fare_for_trips_over_10_miles():
    output, tools = await ask("What is the average fare for trips longer than 10 miles?")
    expected = scalar("SELECT AVG(fare_amount) FROM trips WHERE trip_distance > 10")[0]
    check_tool_order(tools)
    sql = output.sql_query.lower()
    assert "fare_amount" in sql and "trip_distance" in sql
    assert contains_number(output.result_text, expected, tol=0.01), f"expected ~{expected:.4f}"


@pytest.mark.asyncio
async def test_trips_with_zero_passengers():
    output, tools = await ask("How many trips had zero passengers recorded?")
    expected = scalar("SELECT COUNT(*) FROM trips WHERE passenger_count = 0")[0]
    check_tool_order(tools)
    # The agent must filter on passenger_count
    assert "passenger_count" in output.sql_query.lower()
    assert contains_number(output.result_text, expected, tol=0)


@pytest.mark.asyncio
async def test_busiest_day_of_week():
    output, tools = await ask("What is the busiest day of the week for taxi trips?")
    day, cnt = scalar(
        "SELECT dayname(tpep_pickup_datetime) d, COUNT(*) c FROM trips GROUP BY d ORDER BY c DESC LIMIT 1"
    )
    check_tool_order(tools)
    assert "tpep_pickup_datetime" in output.sql_query.lower()
    assert day.lower() in output.result_text.lower()
    assert contains_number(output.result_text, cnt, tol=0)

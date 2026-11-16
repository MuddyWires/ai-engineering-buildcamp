from pydantic import BaseModel, Field
from pydantic_ai import Agent

from utils import collect_tools


judge_instructions = """
You are an expert judge evaluating the performance of an
AI agent.
""".strip()


class JudgeCriterion(BaseModel):
    criterion_description: str = Field(description="The requirement being evaluated.")
    passed: bool = Field(description="Whether the agent satisfied this requirement.")
    judgement: str = Field(description="Why it passed or failed, citing evidence.")


class JudgeFeedback(BaseModel):
    criteria: list[JudgeCriterion] = Field(description="One evaluation per criterion.")
    feedback: str = Field(description="Overall summary of the agent's performance.")


def create_judge_agent():
    return Agent(
        name="judge",
        model="openai:gpt-5.4-nano",
        instructions=judge_instructions,
        output_type=JudgeFeedback,
    )


judge_user_prompt_template = """
Evaluate the agent's performance based on the following criteria:
<CRITERIA>
{criteria}
</CRITERIA>

The agent's final output was:
<AGENT_OUTPUT>
{output}
</AGENT_OUTPUT>

Tool calls:
<TOOL_CALLS>
{tool_calls}
</TOOL_CALLS>
""".strip()


async def evaluate_agent_performance(result, criteria) -> JudgeFeedback:
    tool_calls = collect_tools(result.new_messages())
    prompt = judge_user_prompt_template.format(
        criteria="\n".join(criteria),
        output=result.output.model_dump_json(),
        tool_calls="\n".join(str(tc) for tc in tool_calls),
    )
    judge_result = await create_judge_agent().run(prompt)
    return judge_result.output


async def assert_criteria(result, criteria):
    feedback = await evaluate_agent_performance(result, criteria)
    print("judge feedback:", feedback.feedback)
    for c in feedback.criteria:
        print(f"{c.criterion_description}: {c.judgement}")
        assert c.passed, f"{c.criterion_description}: {c.judgement}"

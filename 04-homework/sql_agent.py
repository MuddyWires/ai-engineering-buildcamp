from dataclasses import dataclass

import pydantic_ai
from pydantic_ai import Agent
import pydantic
from pydantic import BaseModel, Field
from  sql_tools import SQLTools

DEFAULT_INSTRUCTIONS = """ """

@dataclass
class DocumentationAgentConfig:
    model: str = 'openai:gpt-5.4-nano'
    name: str = 'search'
    instructions: str = DEFAULT_INSTRUCTIONS


class SQLResult(BaseModel):
    """
        This model provides a structured answer with metadata about the sql query , the result text and the row count,
        
    """
    
    sql_query: str = Field(description="The sql query run ")
    result_text: str = Field(description="Result text")
    row_count: int = Field(description="Number of rows row_count")


def create_agent()->Agent:
    sqlTools=SQLTools()
    tools=[sqlTools.get_schema, sqlTools.run_sql]
    dbAgent=Agent(
        model=DocumentationAgentConfig.model,
        name=DocumentationAgentConfig.name,
        instructions=DocumentationAgentConfig.instructions,
        tools=tools,
    )
    return dbAgent

async def run_agent(user_prompt):
    llm_prompt=user_prompt
    agent= create_agent()
    result = await agent.run(
        output_type=SQLResult,
        user_prompt=llm_prompt  
    )  
    return result

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(run_agent("What's the average trip distance for rides with 2 passengers?"))
    print(result.output)
    
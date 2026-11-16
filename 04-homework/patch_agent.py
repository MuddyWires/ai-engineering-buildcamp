"""Records token usage and cost of every pydantic-ai Agent.run() call (agent + judge)."""
from collections import defaultdict

from genai_prices import Usage, calc_price
from pydantic_ai import Agent, RunUsage

usages: dict[str, RunUsage] = defaultdict(RunUsage)
calls: dict[str, int] = defaultdict(int)

_original_run = Agent.run


def _model_name(agent) -> str:
    model = agent.model
    return model if isinstance(model, str) else f"{model.system}:{model.model_name}"


async def _tracking_run(self, *args, **kwargs):
    result = await _original_run(self, *args, **kwargs)
    name = _model_name(self)
    usages[name] += result.usage
    calls[name] += 1
    return result


Agent.run = _tracking_run


def calculate_cost(model: str, usage: RunUsage) -> float:
    provider, _, model_ref = model.partition(":")
    price = calc_price(
        Usage(
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_read_tokens=usage.cache_read_tokens,
        ),
        model_ref=model_ref,
        provider_id=provider,
    )
    return float(price.total_price)


def display_total_usage():
    print("\n==== LLM cost ====")
    total = 0.0
    for model, usage in usages.items():
        cost = calculate_cost(model, usage)
        total += cost
        print(f"{model}: {calls[model]} calls, {usage.input_tokens:,} in / "
              f"{usage.output_tokens:,} out tokens -> ${cost:.6f}")
    print(f"Total cost: ${total:.6f}")

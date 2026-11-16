from pydantic_ai import RunUsage


MODEL_PRICES = {
    "openai:gpt-5.4-nano": {"input": 0.20, "output": 1.25},
}


def calculate_cost(model_name, input_tokens, output_tokens):
    prices = MODEL_PRICES[model_name.lower()]
    input_cost = (input_tokens / 1_000_000) * prices["input"]
    output_cost = (output_tokens / 1_000_000) * prices["output"]
    return input_cost + output_cost


from collections import defaultdict

usages = defaultdict(RunUsage)

def capture_usage(model, result):
    usages[model] += result.usage


def display_total_usage():
    print()

    total_cost = 0
    
    for model, usage in usages.items():
        cost = calculate_cost(model, usage.input_tokens, usage.output_tokens)
        print(f"{model}: ${cost:.6f}")
        total_cost += cost
    
    print(f"Total cost: ${total_cost:.6f}")
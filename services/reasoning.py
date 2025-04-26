from utils.openai_client import classify_reasoning_and_intent


def get_reasoning_category_and_intent(question):
    reasoning_output = classify_reasoning_and_intent(question)

    # Initialize variables
    reasoning_type = None
    reasoning_justification = None
    intent = None
    intent_justification = None

    # Parse the LLM output line by line
    for line in reasoning_output.split('\n'):
        line = line.strip()
        if line.lower().startswith("reasoning type:"):
            reasoning_type = line.split(":", 1)[1].strip()
        elif line.lower().startswith("reasoning justification:"):
            reasoning_justification = line.split(":", 1)[1].strip()
        elif line.lower().startswith("intent:"):
            intent = line.split(":", 1)[1].strip()
        elif line.lower().startswith("intent justification:"):
            intent_justification = line.split(":", 1)[1].strip()

    return {
        "reasoning_type": reasoning_type,
        "reasoning_justification": reasoning_justification,
        "intent": intent,
        "intent_justification": intent_justification
    }


import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


def call_llm(prompt):
    """
    Calls the OpenAI LLM API with the given prompt and returns a structured response.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        reply = response['choices'][0]['message']['content'].strip()
        return reply
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None



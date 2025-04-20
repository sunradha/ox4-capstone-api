import openai
from fastapi import HTTPException
from config import settings
import json

# Set your OpenAI API key
openai.api_key = settings.OPENAI_KEY


async def query_openai_reasoning(formatted_data: dict, question: str) -> dict:
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a process mining and data analysis expert. Analyze the provided data and answer the question with detailed insights."
            },
            {
                "role": "user",
                "content": f"I have the following data:\n{json.dumps(formatted_data, indent=2)}\n\nQuestion: {question}"
            }
        ]

        response = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=messages,
            temperature=0.2,
            max_tokens=1500
        )

        return {
            "analysis": response.choices[0].message.content,
            "reasoning_path": "OpenAI reasoning process applied to structured data"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

from openai import AsyncOpenAI
from config import settings
from storage import PROMPTS, state

client = AsyncOpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


async def get_ai_reply(user_message: str, user_name: str) -> str:
    prompt = PROMPTS.get(state.active_prompt, PROMPTS["default"])
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user",   "content": f"{user_name}: {user_message}"}
        ],
        max_tokens=350,
        temperature=0.7
    )
    return response.choices[0].message.content

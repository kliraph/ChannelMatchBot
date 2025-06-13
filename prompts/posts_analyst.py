from openai import OpenAI
from fetcher.posts_fetcher import fetch_posts
from typing import List
import json

# Make sure you’ve set your API key in the environment:
# export OPENAI_API_KEY="sk-…"
#openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_API_KEY = ***REMOVED***
client = OpenAI(api_key=OPENAI_API_KEY)

async def analyze_posts(addresses: List, model="gpt-4o-mini") -> str:

    system_prompt = '''
        Ты эксперт по Telegram и маркетингу. Проанализируй посты канала по следующим критериям: no_swearing, no_gore, topicality, no_contradiction, tone_of_voice. 
        Отвечай по-русски.
        Верни свои результаты с помощью вызова функции analyze_channel. 
    '''

    # Define tools
    fetch_posts_def = {
    "name": "fetch_posts",
    "description": "Return posts for the given channel",
    "parameters": {
        "type":"object",
        "properties":{
        "address":{"type":"string"}
        },
        "required":["address"]
    }
    }

    analyze_channel_def = {
    "type": "function",
    "name": "analyze_channel",
    "description": "Evaluate a Telegram channel's posts against content and tone criteria.",
    "parameters": {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "Channel handle (e.g., '@example_channel')."
            },
            "scores": {
                "type": "object",
                "description": "Numeric scores (1–5) for each criterion.",
                "properties": {
                    "no_swearing": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Absence of profanity."
                    },
                    "no_gore": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Absence of graphic violence."
                    },
                    "topicality": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Alignment with channel theme and name."
                    },
                    "no_contradiction": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Consistency with declared channel stance."
                    },
                    "tone_of_voice": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Consistency and appropriateness of tone."
                    }
                },
                "required": [
                    "no_swearing",
                    "no_gore",
                    "topicality",
                    "no_contradiction",
                    "tone_of_voice"
                ],
                "additionalProperties": False
            },
            "comments": {
                "type": "object",
                "description": "Justifications for each score (1–2 sentences).",
                "properties": {
                    "no_swearing": {"type": "string"},
                    "no_gore": {"type": "string"},
                    "topicality": {"type": "string"},
                    "no_contradiction": {"type": "string"},
                    "tone_of_voice": {"type": "string"}
                },
                "required": [
                    "no_swearing",
                    "no_gore",
                    "topicality",
                    "no_contradiction",
                    "tone_of_voice"
                ],
                "additionalProperties": False
            }
        },
        "required": ["address", "scores", "comments"],
        "additionalProperties": False
    }
}

    analyses = []
    for channel in addresses:
        resp = client.responses.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": channel['address']}
            ],
            functions=[fetch_posts_def, analyze_channel_def],
            function_call="auto"
        )

        tool_calls = resp.tool_calls or []
        # Did the model decide to call fetch_posts?
        if tool_calls and tool_calls[0].name == "fetch_posts":
            args = tool_calls[0].arguments
            addr = args["address"]

            posts = await fetch_posts(addr)

            # Feed the posts back to the model as a tool message
            resp2 = client.responses.create(
                model=model,
                input=[
                    *resp.input,   # system + user + model’s fetch_posts call
                    {
                        "role": "function",
                        "name": "fetch_posts",
                        "content": json.dumps(posts, ensure_ascii=False)
                    }
                ],
                tools=[analyze_channel_def],
                function_call="auto"
            )

            # Finally, extract the analyze_channel arguments
            call2 = resp2.tool_calls[0]
            analysis = call2.arguments
            analyses.append({ **channel, **analysis })

        else:
            analyses.append({ **channel, "error": "no fetch_posts call" })

    return analyses






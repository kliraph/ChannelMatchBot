from openai import OpenAI
from fetcher.posts_fetcher import fetch_posts
from typing import List
import json
from dotenv import load_dotenv
import os

# Инициализация клиента
load_dotenv(override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def analyze_posts(addresses: List[str], model="gpt-4o-mini") -> str:

    system_prompt = '''
        Ты эксперт по Telegram и маркетингу. Проанализируй посты канала по следующим критериям: no_swearing, no_gore, topicality, no_contradiction, tone_of_voice. 
        Отвечай по-русски.
        Верни свои результаты с помощью вызова функции analyze_channel. 
    '''

    # Define tools
    fetch_posts_def = {
    "type": "function",
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
        # Initial model call to determine what to do
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": channel}
            ],
            tools=[fetch_posts_def],
            tool_choice="required"
        )

        # Find any function call in the output
        func_calls = [item for item in resp.output if item.type == "function_call"]

        if func_calls and func_calls[0].name == "fetch_posts":
            fc = func_calls[0]
            args = json.loads(fc.arguments)
            addr = args.get("address")

            try:
                posts = await fetch_posts(addr)
            except Exception as e:
                analyses.append({**channel, "error": f"fetch_posts failed: {e}"})
                continue

            # Send function call output to model for analysis
            function_response = {
                "type": "function_call_output",
                "call_id": fc.call_id,
                "output": json.dumps(posts, ensure_ascii=False),
            }

            # Include earlier messages + function result
            resp2 = client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": channel},
                    fc,
                    function_response
                ],
                tools=[analyze_channel_def],
                tool_choice="required"
            )

            # Extract analysis function call
            func_calls2 = [item for item in resp2.output if item.type == "function_call"]
            if func_calls2 and func_calls2[0].name == "analyze_channel":
                analysis_args = json.loads(func_calls2[0].arguments)
                #analyses.append({**channel, **analysis_args})              
            else:
                #analyses.append({**channel, "error": "no analyze_channel call"})
                analysis_args = {"error": "no analyze_channel call"}
        else:
            #analyses.append({**channel, "error": "no fetch_posts call"})
            analysis_args = {"error": "no fetch_posts call"}
        record = {"address": channel}
        record.update(analysis_args)
        analyses.append(record) 

    return analyses






"""Exercise existing prompt versions and restore production to its original version."""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv('.env')

import httpx
from langfuse import get_client
from app.main import app


def labels(prompt, *extra):
    return sorted((set(prompt.labels) | set(extra)) - {'latest'})


async def run():
    client = get_client()
    name = os.getenv('LANGFUSE_PROMPT_NAME', 'day13-chat')
    original = client.get_prompt(name, label='production', cache_ttl_seconds=0)
    baseline = client.get_prompt(name, version=1, cache_ttl_seconds=0)
    candidate = client.get_prompt(name, version=2, cache_ttl_seconds=0)
    payload = {'user_id': 'student-2A202602721', 'session_id': 'cp2-prompt-comparison', 'feature': 'qa', 'message': 'Explain observability'}
    try:
        client.update_prompt(name=name, version=1, new_labels=labels(baseline, 'baseline'))
        client.update_prompt(name=name, version=2, new_labels=labels(candidate, 'candidate'))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://lab') as api:
            for label, version in [('baseline', 1), ('candidate', 2), ('production', 2)]:
                if label == 'production':
                    prompt = client.get_prompt(name, version=2, cache_ttl_seconds=0)
                    client.update_prompt(name=name, version=2, new_labels=labels(prompt, 'production'))
                client.clear_prompt_cache()
                os.environ['LANGFUSE_PROMPT_LABEL'] = label
                response = await api.post('/chat', json=payload)
                response.raise_for_status()
                print(label, 'version', version, 'correlation_id', response.json()['correlation_id'])
    finally:
        current = client.get_prompt(name, version=original.version, cache_ttl_seconds=0)
        client.update_prompt(name=name, version=original.version, new_labels=labels(current, 'production'))
        client.clear_prompt_cache()
        client.flush()
        print('Restored production version', original.version)


if __name__ == '__main__':
    asyncio.run(run())

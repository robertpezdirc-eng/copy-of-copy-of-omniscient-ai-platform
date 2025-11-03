# 🔄 API Migration Guide - OpenAI & Anthropic SDK Updates
## Developer Guide for Code Updates

**Purpose:** Help developers migrate code from old to new SDK versions  
**Audience:** Backend developers, AI engineers  
**Last Updated:** November 3, 2025

---

## 📋 Overview

This guide covers the breaking changes and required code updates for:
- **OpenAI SDK:** v0.28.x → v1.54.0 (major version upgrade)
- **Anthropic SDK:** v0.7.8 → v0.39.0 (minor version, some changes)

---

## 🔴 OpenAI SDK Migration (v0.x → v1.54.0)

### Breaking Changes Summary

1. **Client-based API** - No more global `openai.api_key`
2. **Response format** - Objects instead of dictionaries
3. **Method names** - New naming conventions
4. **Import structure** - New import paths

### 1. Client Initialization

#### ❌ OLD CODE (v0.28.x)
```python
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORG_ID")
```

#### ✅ NEW CODE (v1.54.0)
```python
from openai import OpenAI, AsyncOpenAI

# Synchronous client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    organization=os.getenv("OPENAI_ORG_ID")  # Optional
)

# Async client (recommended for FastAPI)
async_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
```

### 2. Chat Completions

#### ❌ OLD CODE
```python
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,
    max_tokens=100
)

# Access response
message = response['choices'][0]['message']['content']
usage = response['usage']
```

#### ✅ NEW CODE (Sync)
```python
response = client.chat.completions.create(
    model="gpt-4o",  # Latest model!
    messages=[
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,
    max_tokens=100
)

# Access response (object attributes, not dict keys)
message = response.choices[0].message.content
usage = response.usage
prompt_tokens = response.usage.prompt_tokens
completion_tokens = response.usage.completion_tokens
```

#### ✅ NEW CODE (Async - Recommended)
```python
response = await async_client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,
    max_tokens=100
)

message = response.choices[0].message.content
```

### 3. Embeddings

#### ❌ OLD CODE
```python
response = openai.Embedding.create(
    input="Hello world",
    model="text-embedding-ada-002"
)

embedding = response['data'][0]['embedding']
```

#### ✅ NEW CODE (Sync)
```python
response = client.embeddings.create(
    input="Hello world",
    model="text-embedding-3-small"  # Latest, cost-effective model
)

embedding = response.data[0].embedding
```

#### ✅ NEW CODE (Async)
```python
response = await async_client.embeddings.create(
    input="Hello world",
    model="text-embedding-3-small"
)

embedding = response.data[0].embedding
```

#### Batch Embeddings
```python
# Multiple texts at once
texts = ["Hello", "World", "AI"]
response = await async_client.embeddings.create(
    input=texts,
    model="text-embedding-3-small"
)

embeddings = [item.embedding for item in response.data]
```

### 4. Streaming Responses

#### ❌ OLD CODE
```python
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in response:
    content = chunk['choices'][0].get('delta', {}).get('content')
    if content:
        print(content, end='')
```

#### ✅ NEW CODE (Async)
```python
stream = await async_client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

async for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end='')
```

### 5. Function Calling (Tools)

#### ❌ OLD CODE
```python
functions = [
    {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            }
        }
    }
]

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    functions=functions,
    function_call="auto"
)
```

#### ✅ NEW CODE
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                }
            }
        }
    }
]

response = await async_client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools,
    tool_choice="auto"
)

# Check for tool calls
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
```

### 6. Error Handling

#### ❌ OLD CODE
```python
import openai

try:
    response = openai.ChatCompletion.create(...)
except openai.error.OpenAIError as e:
    print(f"Error: {e}")
```

#### ✅ NEW CODE
```python
from openai import OpenAIError, APIError, RateLimitError

try:
    response = await async_client.chat.completions.create(...)
except RateLimitError as e:
    print(f"Rate limited: {e}")
except APIError as e:
    print(f"API error: {e}")
except OpenAIError as e:
    print(f"OpenAI error: {e}")
```

### 7. New Models Available

```python
# Latest GPT-4 models
models = [
    "gpt-4o",              # Best for most tasks
    "gpt-4o-mini",         # Fast and cost-effective
    "gpt-4-turbo",         # Previous flagship
    "gpt-4",               # Original GPT-4
    "gpt-3.5-turbo"        # Fast and cheap
]

# Latest embedding models
embedding_models = [
    "text-embedding-3-small",  # 1536 dims, cost-effective
    "text-embedding-3-large",  # 3072 dims, best quality
    "text-embedding-ada-002"   # Legacy, still supported
]
```

---

## 🟣 Anthropic SDK Migration (v0.7.8 → v0.39.0)

### Breaking Changes Summary

1. **Messages API** - New primary API (replaces completion API)
2. **Client initialization** - Similar to OpenAI v1.x pattern
3. **Model names** - New Claude 3.5 models

### 1. Client Initialization

#### ❌ OLD CODE (v0.7.8)
```python
import anthropic

client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

#### ✅ NEW CODE (v0.39.0)
```python
from anthropic import Anthropic, AsyncAnthropic

# Synchronous client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Async client (recommended for FastAPI)
async_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

### 2. Text Generation (Completion → Messages)

#### ❌ OLD CODE (Completion API)
```python
response = client.completion(
    prompt=f"{anthropic.HUMAN_PROMPT} Hello! {anthropic.AI_PROMPT}",
    model="claude-2",
    max_tokens_to_sample=100
)

text = response['completion']
```

#### ✅ NEW CODE (Messages API)
```python
response = await async_client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

text = response.content[0].text
```

### 3. System Prompts

#### ❌ OLD CODE
```python
prompt = f"{anthropic.HUMAN_PROMPT} You are a helpful assistant.\n\nHello! {anthropic.AI_PROMPT}"
response = client.completion(prompt=prompt, model="claude-2")
```

#### ✅ NEW CODE
```python
response = await async_client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system="You are a helpful assistant.",  # System prompt separate
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)
```

### 4. Streaming

#### ❌ OLD CODE
```python
response = client.completion_stream(
    prompt=f"{anthropic.HUMAN_PROMPT} Tell me a story {anthropic.AI_PROMPT}",
    model="claude-2"
)

for data in response:
    print(data['completion'], end='')
```

#### ✅ NEW CODE
```python
async with async_client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Tell me a story"}]
) as stream:
    async for text in stream.text_stream:
        print(text, end='')
```

### 5. Multi-turn Conversations

#### ✅ NEW CODE
```python
messages = [
    {"role": "user", "content": "What's 2+2?"},
    {"role": "assistant", "content": "2+2 equals 4."},
    {"role": "user", "content": "What about 3+3?"}
]

response = await async_client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=messages
)
```

### 6. Response Structure

```python
response = await async_client.messages.create(...)

# Access response data
text = response.content[0].text
model_used = response.model
stop_reason = response.stop_reason  # "end_turn", "max_tokens", etc.

# Usage statistics
input_tokens = response.usage.input_tokens
output_tokens = response.usage.output_tokens
```

### 7. New Claude 3.5 Models

```python
models = [
    "claude-3-5-sonnet-20241022",  # Latest, most capable
    "claude-3-opus-20240229",      # Previous flagship
    "claude-3-sonnet-20240229",    # Balanced
    "claude-3-haiku-20240307"      # Fast and cheap
]

# Use latest model
response = await async_client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,  # Claude 3.5 supports up to 8192
    messages=[...]
)
```

---

## 🔧 FastAPI Integration Examples

### Complete RAG Service Example

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import os

app = FastAPI()

# Initialize clients
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class QueryRequest(BaseModel):
    query: str
    provider: str = "openai"  # or "anthropic"
    model: str | None = None

@app.post("/api/v1/query")
async def query_llm(request: QueryRequest):
    """Query LLM with automatic provider switching"""
    
    if request.provider == "openai":
        model = request.model or "gpt-4o"
        try:
            response = await openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": request.query}],
                max_tokens=500
            )
            return {
                "answer": response.choices[0].message.content,
                "model": model,
                "provider": "openai",
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    elif request.provider == "anthropic":
        model = request.model or "claude-3-5-sonnet-20241022"
        try:
            response = await anthropic_client.messages.create(
                model=model,
                max_tokens=500,
                messages=[{"role": "user", "content": request.query}]
            )
            return {
                "answer": response.content[0].text,
                "model": model,
                "provider": "anthropic",
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    else:
        raise HTTPException(status_code=400, detail="Invalid provider")

@app.post("/api/v1/embeddings")
async def generate_embeddings(texts: list[str]):
    """Generate embeddings using OpenAI"""
    try:
        response = await openai_client.embeddings.create(
            input=texts,
            model="text-embedding-3-small"
        )
        return {
            "embeddings": [item.embedding for item in response.data],
            "model": "text-embedding-3-small",
            "dimension": 1536,
            "count": len(texts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 📝 Checklist for Migration

### For Each File Using OpenAI:
- [ ] Update imports: `from openai import OpenAI, AsyncOpenAI`
- [ ] Initialize client: `client = AsyncOpenAI(api_key=...)`
- [ ] Update method calls: `.chat.completions.create()` not `.ChatCompletion.create()`
- [ ] Update response access: `response.choices[0].message.content` not `response['choices'][0]['message']['content']`
- [ ] Update embedding calls: `client.embeddings.create()` not `openai.Embedding.create()`
- [ ] Use latest models: `gpt-4o`, `text-embedding-3-small`
- [ ] Update error handling: `from openai import OpenAIError`

### For Each File Using Anthropic:
- [ ] Update imports: `from anthropic import Anthropic, AsyncAnthropic`
- [ ] Initialize client: `client = AsyncAnthropic(api_key=...)`
- [ ] Migrate to Messages API: `client.messages.create()`
- [ ] Remove prompt formatting: No more `HUMAN_PROMPT`, `AI_PROMPT`
- [ ] Update model names: `claude-3-5-sonnet-20241022`
- [ ] Update response access: `response.content[0].text`
- [ ] Use `max_tokens` not `max_tokens_to_sample`

---

## 🎯 Testing Your Migration

```python
# Quick test script
import asyncio
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import os

async def test_openai():
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Say 'OpenAI works!'"}],
        max_tokens=10
    )
    print(f"✅ OpenAI: {response.choices[0].message.content}")

async def test_anthropic():
    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = await client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=10,
        messages=[{"role": "user", "content": "Say 'Anthropic works!'"}]
    )
    print(f"✅ Anthropic: {response.content[0].text}")

async def main():
    await test_openai()
    await test_anthropic()

if __name__ == "__main__":
    asyncio.run(main())
```

Run: `python test_migration.py`

---

## 📚 Additional Resources

- [OpenAI v1.x Migration Guide](https://github.com/openai/openai-python/discussions/742)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic Messages API](https://docs.anthropic.com/claude/reference/messages_post)
- [Claude 3.5 Sonnet Release Notes](https://www.anthropic.com/claude)

---

**Document Version:** 1.0  
**Last Updated:** November 3, 2025  
**Status:** Ready for Use

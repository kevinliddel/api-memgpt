import anyio

async def stream_response(content: str):
    for word in content.split():
        yield f"{word} "

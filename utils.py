import anyio

async def stream_response(content: str):
    for line in content.split('\n'):
        yield f"{line}\n"

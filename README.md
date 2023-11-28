# MEMGPT Restapi

Installation and deployment:

1. Copy .env.exemple to .env and fill it with your apikey and you frontend uri.

2. Execute those commands:

- `pip install -r requirements.txt`

- `PYTHONPATH=. uvicorn main:app`

- `uvicorn main:app`

# Usage : 

### Session
- get session_id on `GET /chat/init`

### Chats
- connect to websocket on `WS /chat/socket/{session_id}`
- streaming responses: `POST /chat/stream/{session_id}`

### Memory
- retreive recall memory stats : `GET /memory/{session_id}/recall/stats`
- TO DO : 
    - archival  memory
    - search on memory 

Using docker: 

```s
docker build -t memgpt .
```

```s
docker run -v $PWD:/usr/src/app -p 8000:8000 --name memgpt0 memgpt
```


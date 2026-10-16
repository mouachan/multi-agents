"""The chat: conversations with the agents, routed message by message.

    sessions.py   conversations (create, list, read, delete), private to their owner
    turn.py       one message: routing, the agent's streamed answer, saving it with its trace
    routing.py    which agent profile answers a message (semantic routing, keywords as fallback)
    prompts.py    the prompt editor: the profile's MLflow prompt, or a per-conversation override
    config.py     texts and suggested actions (files/prompts/backend/chat-config.yaml)
"""

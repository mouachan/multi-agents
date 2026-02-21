#!/usr/bin/env python3
"""Quick test for ReActAgent with correct MCP tool format."""
import os
import time

os.environ.setdefault("LLAMASTACK_ENDPOINT", "http://claims-llamastack-service.multi-agents.svc.cluster.local:8321")
os.environ.setdefault("LLAMASTACK_DEFAULT_MODEL", "vllm-inference-1/llama-instruct-32-3b")

from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.react.agent import ReActAgent
from llama_stack_client.lib.agents.event_logger import EventLogger

def test_react_with_mcp():
    print("Testing ReActAgent with MCP tools (correct format)...")
    client = LlamaStackClient(base_url=os.environ["LLAMASTACK_ENDPOINT"])

    tools = [
        {
            "type": "mcp",
            "server_label": "ocr-server",
            "server_url": "http://ocr-server.multi-agents.svc.cluster.local:8080/sse"
        },
        {
            "type": "mcp",
            "server_label": "rag-server",
            "server_url": "http://rag-server.multi-agents.svc.cluster.local:8080/sse"
        }
    ]

    try:
        start = time.time()
        agent = ReActAgent(
            client=client,
            model=os.environ["LLAMASTACK_DEFAULT_MODEL"],
            tools=tools,
            instructions="You are a claims processing assistant.",
        )
        print(f"✓ Agent created in {time.time() - start:.2f}s")

        session_id = agent.create_session("test-mcp")
        print(f"✓ Session created: {session_id}")

        print("Running turn...")
        turn_start = time.time()
        response = agent.create_turn(
            messages=[{"role": "user", "content": "What tools do you have? Just list them."}],
            session_id=session_id,
            stream=False,
        )

        final_content = None
        for log in EventLogger().log(response):
            print(f"  Event: {log}")
            if hasattr(log, 'role') and log.role == "assistant":
                final_content = str(log)

        print(f"✓ Turn completed in {time.time() - turn_start:.2f}s")
        print(f"✓ Response: {final_content}")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_react_with_mcp()
    exit(0 if success else 1)

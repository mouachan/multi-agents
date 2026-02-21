#!/usr/bin/env python3
"""
Simple test script to verify ReActAgent functionality with LlamaStack.
Run this directly in the backend pod to test vLLM calls.
"""

import os
import time
import sys

# Set environment variables if needed
os.environ.setdefault("LLAMASTACK_ENDPOINT", "http://claims-llamastack-service.multi-agents.svc.cluster.local:8321")
os.environ.setdefault("LLAMASTACK_DEFAULT_MODEL", "vllm-inference-1/llama-instruct-32-3b")

from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.react.agent import ReActAgent

def test_simple_generation():
    """Test simple text generation without agents."""
    print("\n=== Test 1: Simple text generation ===")
    client = LlamaStackClient(
        base_url=os.environ["LLAMASTACK_ENDPOINT"]
    )

    try:
        start = time.time()
        response = client.inference.chat_completion(
            model_id=os.environ["LLAMASTACK_DEFAULT_MODEL"],
            messages=[
                {"role": "user", "content": "Say 'Hello, I am working!' in one short sentence."}
            ],
            max_tokens=50
        )
        duration = time.time() - start

        content = response.completion_message.content
        print(f"✓ Response: {content}")
        print(f"✓ Duration: {duration:.2f}s")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_react_agent_without_tools():
    """Test ReActAgent without any tools."""
    print("\n=== Test 2: ReActAgent without tools ===")
    client = LlamaStackClient(
        base_url=os.environ["LLAMASTACK_ENDPOINT"]
    )

    try:
        start = time.time()

        # Create ReActAgent without tools
        agent = ReActAgent(
            client=client,
            model=os.environ["LLAMASTACK_DEFAULT_MODEL"],
            tools=[],  # No tools
            instructions="You are a helpful assistant. Answer questions concisely.",
        )

        print(f"✓ Agent created in {time.time() - start:.2f}s")

        # Create session
        session_start = time.time()
        session_id = agent.create_session("test-session")
        print(f"✓ Session created in {time.time() - session_start:.2f}s: {session_id}")

        # Run a simple turn
        turn_start = time.time()
        response = agent.create_turn(
            messages=[{"role": "user", "content": "What is 2+2? Answer in one sentence."}],
            session_id=session_id,
            stream=False,
        )

        # Parse response
        from llama_stack_client.lib.agents.event_logger import EventLogger
        final_content = None
        for log in EventLogger().log(response):
            if hasattr(log, 'role') and log.role == "assistant":
                final_content = str(log)
                break

        duration = time.time() - turn_start
        print(f"✓ Turn completed in {duration:.2f}s")
        print(f"✓ Response: {final_content}")

        total_duration = time.time() - start
        print(f"✓ Total duration: {total_duration:.2f}s")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_react_agent_with_mcp_tools():
    """Test ReActAgent with MCP toolgroups."""
    print("\n=== Test 3: ReActAgent with MCP tools ===")
    client = LlamaStackClient(
        base_url=os.environ["LLAMASTACK_ENDPOINT"]
    )

    try:
        start = time.time()

        # Create ReActAgent with MCP tools
        tools = [
            {"toolgroup_id": "mcp::ocr-server"},
            {"toolgroup_id": "mcp::rag-server"}
        ]

        agent = ReActAgent(
            client=client,
            model=os.environ["LLAMASTACK_DEFAULT_MODEL"],
            tools=tools,
            instructions="You are a claims processing assistant. Use available tools to process insurance claims.",
        )

        print(f"✓ Agent created with MCP tools in {time.time() - start:.2f}s")

        # Create session
        session_start = time.time()
        session_id = agent.create_session("test-mcp-session")
        print(f"✓ Session created in {time.time() - session_start:.2f}s: {session_id}")

        # Run a simple turn that might use tools
        turn_start = time.time()
        print("Running turn (this may take a while)...")

        response = agent.create_turn(
            messages=[{
                "role": "user",
                "content": "Hello, can you tell me what tools you have available? Just list them briefly."
            }],
            session_id=session_id,
            stream=False,
        )

        # Parse response
        from llama_stack_client.lib.agents.event_logger import EventLogger
        final_content = None
        for log in EventLogger().log(response):
            print(f"  Event: {log}")
            if hasattr(log, 'role') and log.role == "assistant":
                final_content = str(log)

        duration = time.time() - turn_start
        print(f"✓ Turn completed in {duration:.2f}s")
        print(f"✓ Response: {final_content}")

        total_duration = time.time() - start
        print(f"✓ Total duration: {total_duration:.2f}s")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("LlamaStack ReActAgent Test Suite")
    print("=" * 60)
    print(f"LlamaStack Endpoint: {os.environ['LLAMASTACK_ENDPOINT']}")
    print(f"Model: {os.environ['LLAMASTACK_DEFAULT_MODEL']}")
    print("=" * 60)

    results = []

    # Test 1: Simple generation
    results.append(("Simple generation", test_simple_generation()))

    # Test 2: ReActAgent without tools
    results.append(("ReActAgent (no tools)", test_react_agent_without_tools()))

    # Test 3: ReActAgent with MCP tools
    results.append(("ReActAgent (MCP tools)", test_react_agent_with_mcp_tools()))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")

    # Exit code
    sys.exit(0 if all(r[1] for r in results) else 1)

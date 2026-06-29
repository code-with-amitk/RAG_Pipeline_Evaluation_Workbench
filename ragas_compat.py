"""
ragas_compat.py
Patch missing langchain_community stubs required by ragas 0.4.3.

Newer langchain-community releases removed chat_models.vertexai, but ragas
still imports it at module load time. This stub satisfies that import.
"""

import sys
import types


def patch_ragas_imports() -> None:
    if "langchain_community.chat_models.vertexai" in sys.modules:
        return

    vertexai_mod = types.ModuleType("langchain_community.chat_models.vertexai")

    class ChatVertexAI:  # noqa: D101 - stub for isinstance checks in ragas
        """Stub class; not used by this project."""

    vertexai_mod.ChatVertexAI = ChatVertexAI
    sys.modules["langchain_community.chat_models.vertexai"] = vertexai_mod


patch_ragas_imports()

"""
title: Long Term Memory Filter using Ollama and Local Neo4j GraphDB
author: BrainDriveAI
date: 2024-10-30
version: 1.0
license: MIT
description:
    This pipeline implements a long-term memory system that processes and stores user messages using the mem0 framework.
    It integrates with:
      - Neo4j GraphDB as a local graph database for memory context organization and management.
      - Ollama LLM for language model capabilities, including embedding and contextual generation, utilizing the 
        `llama3.1:latest` model for tool-calling support.
      - Ollama's embedding models
    The filter periodically consolidates user messages into memory based on a configurable cycle and retrieves relevant 
    memories to enhance conversational context.
    Adapted from: https://github.com/open-webui/pipelines/blob/main/examples/filters/mem0_memory_filter_pipeline.py

requirements: pydantic==2.7.4, mem0ai, rank-bm25, neo4j
"""

# Troubleshooting Note:
# I encountered the following error when installing the mem0 pipeline example locally:
#
#   FieldValidatorDecoratorInfo.__init__() got an unexpected keyword argument
#   'json_schema_input_type'
#
# Upgrading Pydantic to version 2.7.4 resolved the issue. To upgrade Pydantic inside the
# pipeline’s Docker container, use the following command:
#
#   pip install --upgrade pydantic==2.7.4
#
# Hope this helps anyone facing the same problem!
# Refer to this issue https://github.com/open-webui/pipelines/issues/272#issuecomment-2424067820


from typing import List, Optional
from pydantic import BaseModel, Field
import json
from mem0 import Memory
import os

from utils.pipelines.main import get_last_user_message

class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = []
        priority: int = 0

        STORE_CYCLES: int = 5  # Messages count before storing to memory
        MEM_ZERO_USER: str = "username"  # Used internally by mem0
        DEFINE_NUMBER_OF_MEMORIES_TO_USE: int = Field(
            default=5, description="Specify how many memory entries you want to use as context."
        )

        # LLM configuration (Ollama)
         # Default values for the mem0 language model
        OLLAMA_LLM_MODEL: str = "llama3.1:latest" # This model need to exist in ollama and needs to be tool calling model
        OLLAMA_LLM_TEMPERATURE: float = 0
        OLLAMA_LLM_MAX_TOKENS: int = 8000
        OLLAMA_LLM_URL: str = "http://127.0.0.1:11434"

        OLLAMA_EMBEDDER_MODEL = "mxbai-embed-large"

        # Neo4j configuration
        NEO4J_URL = "neo4j://host.docker.internal:7687"
        NEO4J_USER = "neo4j"
        NEO4J_PASSWORD = "my_password123"

    def __init__(self):
        try:
            self.type = "filter"
            self.name = "Memory Filter"
            self.user_messages = []
            self.thread = None
            self.valves = self.Valves(
                pipelines=["*"],
            )
            self.m = None
        except Exception as e:
            print(f"Error initializing Pipeline: {e}")

    async def on_startup(self):
        self.m = self.init_mem_zero()
        pass

    async def on_shutdown(self):
        print(f"on_shutdown: {__name__}")
        pass

    async def inlet(self, body: dict, user: Optional[dict] = None):
        try:
            print(f"pipe: {__name__}")
            # Ensure mem0 instance is available
            # self.m = self.check_or_create_mem_zero()

            user = self.valves.MEM_ZERO_USER
            store_cycles = self.valves.STORE_CYCLES

            if isinstance(body, str):
                body = json.loads(body)

            all_messages = body["messages"]
            last_message = get_last_user_message(all_messages)
            print("Latest user message ", last_message)

            self.user_messages.append(last_message)

            if len(self.user_messages) == store_cycles:
                message_text = " ".join(self.user_messages)

                self.add_memory_thread(message_text=message_text, user=user)

                print("Processing the following text into memory:")
                print(message_text)

                # self.thread.start()
                self.user_messages.clear()

            memories = self.m.search(last_message, user_id=user)

            print(f"Memories: {memories}")

            memory_list = memories.get('memories', [])

            maxMemoriesToJoin = self.valves.DEFINE_NUMBER_OF_MEMORIES_TO_USE

            # Check if there are memories and the list is not empty
            if memory_list:
                # Slice the list to get the first 'n' items and join their 'memory' fields
                fetched_memory = " ".join(memory_item["memory"] for memory_item in memory_list[:maxMemoriesToJoin] if "memory" in memory_item)
                
                if fetched_memory:
                    print("Fetched memories successfully:", fetched_memory)
                else:
                    fetched_memory = ""
            else:
                fetched_memory = ""

            if fetched_memory:
                all_messages.insert(0, {
                    "role": "system",
                    "content": (
                        "This is your inner voice talking. You remember this about the person you're chatting with: "
                        + str(fetched_memory)
                    )
                })

            return body
        except Exception as e:
            print(f"Error in inlet method: {e}")
            return body

    def add_memory_thread(self, message_text, user):
        try:
            # Create a new memory instance to avoid concurrency issues
            # memory_instance = self.init_mem_zero()
            self.m.add(message_text, user_id=user)
        except Exception as e:
            print(f"Error adding memory: {e}")
            

    def check_or_create_mem_zero(self):
        """Verify or reinitialize mem0 instance."""
        try:
            self.m.search("my name", user_id=self.valves.MEM_ZERO_USER)  # Lightweight operation to test instance
            return self.m
        except Exception as e:
            print(f"Mem0 instance error, creating a new one: {e}")
            return self.init_mem_zero()

    def init_mem_zero(self):
        """Initialize a new mem0 instance."""
        try:
            config = {
                "embedder": {
                    "provider": "ollama",
                    "config": {
                        "model": self.valves.OLLAMA_EMBEDDER_MODEL,
                    }
                },
                "graph_store": {
                    "provider": "neo4j",
                    "config": {
                        "url": self.valves.NEO4J_URL,
                        "username": self.valves.NEO4J_USER,
                        "password": self.valves.NEO4J_PASSWORD,
                    },
                },
                "llm": {
                    "provider": "ollama",
                    "config": {
                        "model": self.valves.OLLAMA_LLM_MODEL,
                        "temperature": self.valves.OLLAMA_LLM_TEMPERATURE,
                        "max_tokens": self.valves.OLLAMA_LLM_MAX_TOKENS,
                        "ollama_base_url": self.valves.OLLAMA_LLM_URL
                    }
                },
                "version": "v1.1"
            }

            return Memory.from_config(config_dict=config)
        except Exception as e:
            print(f"Error initializing Memory: {e}")
            raise

"""
title: Long Term Memory Filter using OpenAI and PostgreSQL
author: cicero.app
date: 2024-10-30
version: 1.0
license: MIT
description:
     A filter that processes user messages and stores them as long-term memory by utilizing the mem0 framework.
    It uses a PostgreSQL database with the pgvector extension as the vector store (Supabase), OpenAI as the LLM model,
    and the OpenAI `text-embedding-3-small` as the embedding model.
    Adapted from: https://github.com/open-webui/pipelines/blob/main/examples/filters/mem0_memory_filter_pipeline.py

requirements: pydantic==2.7.4, openai, pgvector, mem0ai
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
import threading
import os
import psycopg2

from utils.pipelines.main import get_last_user_message

class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = []
        priority: int = 0

        OPENAI_API_KEY: str = ""

        STORE_CYCLES: int = 5  # Messages count before storing to memory
        MEM_ZERO_USER: str = "user"  # Used internally by mem0
        DEFINE_NUMBER_OF_MEMORIES_TO_USE: int = Field(
            default=5, description="Specify how many memory entries you want to use as context."
        )

        # PostgreSQL vector store configuration
        POSTGRESQL_USER: str = "postgres"
        POSTGRESQL_DB_NAME: str = "postgres"
        POSTGRESQL_HOST: str = "host.docker.internal"
        POSTGRESQL_PORT: str = "5433"
        POSTGRESQL_PWD: str = "password"
        VECTOR_STORE_EMBEDDING_DIMS: int = 1536  # Must match the embedder model's dimensions

        # LLM configuration (OpenAI)
        OPENAI_LLM_MODEL: str = "gpt-4o"
        OPENAI_LLM_TEMPERATURE: float = 0
        OPENAI_LLM_MAX_TOKENS: int = 2000

        # Embedding model configuration (OpenAI)
        OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    def __init__(self):
        try:
            self.type = "filter"
            self.name = "Memory Filter"
            self.user_messages = []
            self.thread = None
            self.memory_lock = threading.Lock()
            self.valves = self.Valves(
                pipelines=["*"],
                OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", "")
            )
            self.m = None
        except Exception as e:
            print(f"Error initializing Pipeline: {e}")

    def test_supabase_connection(self):
        """Test the connection to the Supabase PostgreSQL database."""
        try:
            conn = psycopg2.connect(
                host=self.valves.POSTGRESQL_HOST,
                port=self.valves.POSTGRESQL_PORT,
                database=self.valves.POSTGRESQL_DB_NAME,
                user=self.valves.POSTGRESQL_USER,
                password=self.valves.POSTGRESQL_PWD,
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")  # Simple query to verify the connection
            result = cursor.fetchone()
            if result and result[0] == 1:
                print("Supabase connection test successful!")
            else:
                print("Supabase connection test failed.")
            cursor.close()
            conn.close()
        except psycopg2.Error as e:
            print(f"Supabase connection error: {e}")

    async def on_startup(self):
        self.test_supabase_connection()
        self.m = self.init_mem_zero()

    async def on_shutdown(self):
        print(f"on_shutdown: {__name__}")
        pass

    async def inlet(self, body: dict, user: Optional[dict] = None):
        try:
            print(f"pipe: {__name__}")
            # Ensure mem0 instance is available
            self.m = self.check_or_create_mem_zero()

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

                if self.thread and self.thread.is_alive():
                    print("Waiting for previous memory thread to finish.")
                    self.thread.join()

                self.thread = threading.Thread(
                    target=self.add_memory_thread,
                    args=(message_text, user),
                )

                print("Processing the following text into memory:")
                print(message_text)

                self.thread.start()
                self.user_messages.clear()

            memories = self.m.search(last_message, user_id=user)

            max_memories_to_join = self.valves.DEFINE_NUMBER_OF_MEMORIES_TO_USE

            # Check if there are memories and the list is not empty
            if memories:
                # Slice the list to get the first 'n' items and join their 'memory' fields
                fetched_memory = " ".join(memory_item["memory"] for memory_item in memories[:max_memories_to_join] if "memory" in memory_item)
                
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
        """Safely add memory using a thread lock."""
        with self.memory_lock:
            try:
                # Create a new memory instance to avoid concurrency issues
                memory_instance = self.init_mem_zero()
                memory_instance.add(message_text, user_id=user, metadata={"category": "conversation"})
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
                "vector_store": {
                    "provider": "pgvector",
                    "config": {
                        "host": self.valves.POSTGRESQL_HOST,
                        "port": self.valves.POSTGRESQL_PORT,
                        "user": self.valves.POSTGRESQL_USER,
                        "password": self.valves.POSTGRESQL_PWD,
                        "embedding_model_dims": self.valves.VECTOR_STORE_EMBEDDING_DIMS,
                    },
                },
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": self.valves.OPENAI_LLM_MODEL,
                        "temperature": self.valves.OPENAI_LLM_TEMPERATURE,
                        "max_tokens": self.valves.OPENAI_LLM_MAX_TOKENS,
                        "api_key": self.valves.OPENAI_API_KEY,
                    }
                },
                "embedder": {
                    "provider": "openai",
                    "config": {
                        "model": self.valves.OPENAI_EMBEDDING_MODEL,
                        "api_key": self.valves.OPENAI_API_KEY,
                        "embedding_dims": self.valves.VECTOR_STORE_EMBEDDING_DIMS,
                    },
                },
            }

            return Memory.from_config(config)
        except Exception as e:
            print(f"Error initializing Memory: {e}")
            raise

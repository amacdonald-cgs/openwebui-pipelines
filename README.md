# Custom Pipelines for OpenWebUI  

Welcome to our collection of **custom OpenWebUI pipelines**! These pipelines extend the capabilities of your OpenWebUI instance by integrating advanced logic, external services, and seamless workflows.

---

## 🚀 Pipelines Overview  
OpenWebUI pipelines enable **modular workflows**, enhancing any UI client that supports OpenAI API specifications. These pipelines handle complex tasks efficiently, integrating Python libraries and custom logic for better performance and flexibility.  

### Available Pipelines  

1. **[Chat with YouTube Pipeline](https://github.com/Digital-Brain-Builders/openwebui-pipelines/blob/main/pipelines/chat-with-youtube-pipeline.py)**  
   - **Description:**  
     This pipeline searches for YouTube videos, retrieves transcripts, generates transcript summaries, enables Q&A over transcripts, and performs search operations within video transcripts.
   - **Features:**  
     - Search for videos similar to YouTube’s built-in search.  
     - Fetch and summarize video transcripts.  
     - Ask questions over video transcripts or search specific moments within them.

2. **[Long-Term Memory Filter Pipeline](https://github.com/Digital-Brain-Builders/openwebui-pipelines/blob/main/pipelines/long-term-memory-filter-pipeline.py)**  
   - **Description:**  
     This pipeline stores user interactions as vectorized memories in **PostgreSQL (pgvector)** for long-term retrieval. It uses **OpenAI LLM** to embed and organize messages.
   - **Features:**  
     - Embeds messages using OpenAI models.  
     - Stores vectorized memories in PostgreSQL with pgvector.  
     - Ideal for chat applications requiring long-term memory and enhanced user interactions.

---

## 📦 Installation and Setup  

To add these pipelines to your OpenWebUI instance, follow these steps:

1. **Copy the GitHub URL** of the pipeline you want to install:  
   - [Chat with YouTube Pipeline URL](https://github.com/Digital-Brain-Builders/openwebui-pipelines/blob/main/pipelines/chat-with-youtube-pipeline.py)  
   - [Long-Term Memory Filter Pipeline URL](https://github.com/Digital-Brain-Builders/openwebui-pipelines/blob/main/pipelines/long-term-memory-filter-pipeline.py)  

2. **Go to Admin Panel -> Settings -> Pipelines** in your OpenWebUI instance.  
3. **Paste the GitHub URL** in the "Install from GitHub URL" field.  
4. **Click the Install / Download icon** to complete the installation.  

---
 
**Troubleshooting Installation Issues:**  
Some users reported encountering the following error:  
```
FieldValidatorDecoratorInfo.__init__() got an unexpected keyword argument 'json_schema_input_type'
```  
To fix this, upgrade `pydantic` to version 2.7.4 inside the Docker container:  
```bash  
pip install --upgrade pydantic==2.7.4  
```

---

## 📚 References  
- [OpenWebUI Pipelines Documentation](https://github.com/open-webui/pipelines)  
- [Supabase PostgreSQL with pgvector](https://supabase.com/docs/guides/database/extensions/pgvector)  
- [OpenAI API Documentation](https://beta.openai.com/docs/)  
- [Mem0 Documentation](https://docs.mem0.ai/overview)
- [Langchain Documentation](https://python.langchain.com/docs/introduction/)
---

## 🌐 License  
This project is licensed under the **MIT License**.

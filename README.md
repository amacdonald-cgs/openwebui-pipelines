 # Custom Pipelines for OpenWebUI  

Welcome to our collection of **custom OpenWebUI pipelines**! These pipelines are designed to enhance your OpenWebUI instance by integrating advanced logic and external services.

---

## 🚀 Pipelines Overview  
OpenWebUI pipelines allow for **modular workflows** to extend the capabilities of any UI client supporting OpenAI API specifications. These pipelines offload computationally intensive tasks, enabling seamless integration of Python libraries and custom logic.  

This repository includes the following pipelines:  
1. **Long-Term Memory Filter:** Stores user interactions as vectorized memories in PostgreSQL (pgvector) using OpenAI models.  
2. **[Additional Pipelines Coming Soon...]**  

Each pipeline is tailored to provide better performance, scalability, and flexibility when compared to default filters or functions available in OpenWebUI.  

---

## 📦 Installation and Setup  

To use these custom pipelines with your OpenWebUI instance, follow these steps:  

## 🧠 Long-Term Memory Filter Pipeline  

This pipeline processes user messages and stores them in **PostgreSQL (pgvector)** for long-term memory retrieval. It utilizes **OpenAI LLMs** to enhance interactions and employs the `text-embedding-3-small` model for embedding messages.

**How to Use:**  
1. Add the pipeline to your OpenWebUI instance using the steps above.  
2. Ensure you have PostgreSQL installed with the `pgvector` extension (we used **Supabase** for our setup).  

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

---

## 🌐 License  
This project is licensed under the **MIT License**.  

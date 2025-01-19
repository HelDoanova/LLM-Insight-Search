# LLM-Insight-Search

Collecting documents from the Internet based on user query using LLM semantic analysis
About The Project - doplnit

## Installation

### 1: Create a Virtual Environment

Run the following command to create a virtual environment in the root directory:

```bash
python -m venv venv
```

Activate the virtual environment(windows):

```bash
venv\Scripts\activate
```

### 2: Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3: Create a `.env` File

Create a `.env` file in the root directory to store your API KEYS. Add the following variables:

```
BRAVE_SEARCH_API_KEY = <your_api_key>
HF_API_KEY = <your_api_key>
FIRECRAWL_API_KEY = <your_api_key>
MONGO_DB_URI = <your_mongo_connection_string>
OPENAI_API_KEY =<your_api_key>
```

Replace `<your_api_key>` with your actual API key for the respective services, and `<your_mongo_connection_string>` with your MongoDB connection string.

## Usage

Ensure that your application has access to the necessary API keys and all dependencies are properly installed.

### 1 Run the Application

```bash
python App.py
```

### 2: Interact with the Application

Interacting with the application is intuitive; simply follow the instructions displayed in the terminal step by step.

-další popsání + výstupy

## Module Replacement

The application is designed with modularity in mind, allowing you to replace individual modules without affecting the overall functionality. Each module can be updated or swapped to suit specific needs.

Replacing a module is simple and requires only minimal adjustments in the main application script `App.py`. Specifically, you need to:

1. **Modify the initialization of the module** in `App.py` to integrate the new implementation.
2. **Ensure function naming consistency**:
   - The functions within the new module must retain the same names as those in the original module, as these are called by the application `App.py` to perform necessary operations.
   - If the new module uses different function names, they must be updated to match the expected names in the application to maintain compatibility with the rest of the system.
3. **Ensure correct data types**:
   - Verify that the functions in the new module accept and return the same data types as the original module. This ensures compatibility with other parts of the application and avoids runtime errors.

This approach ensures that new modules are seamlessly integrated without requiring extensive changes to the core application logic. The modularity provides flexibility and adaptability, making the application suitable for various use cases and future-proof against changes in technology or requirements.

Below are the initializations and required functions for each module.

### Module - Query Optimization

```bash
optimizer = HuggingFaceModule()
optimized_query = optimizer.optimize_query(user_query)
```

### Module - Search on Internet

```bash
search_engine = BraveSearchEngine(result_count=result_count)
urls = search_engine.search(search_query)
```

### Module - Text Extraction

```bash
extractor = FirecrawlExtractor()
document, status_code = extractor.extract_text_from_url(url, level)
```

### Module - Document classification

```bash
 classifier = OpenAI()
 relevance_result = classifier.classify_document(document["markdown"], search_query)
```

### Module - Database

```bash
 database_handler = MongoDB(database_name="default_db",collection_name=filename_search_query)
 database_handler.show_database()
 database_handler.set_database(database_name_new)
 database_handler.set_collection(collection_name_new)
```

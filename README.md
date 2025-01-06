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

The application is designed with modularity in mind, allowing you to replace individual modules without affecting the overall functionality. Each module can be updated or swapped to suit specific needs:

### Module - Query Optimization

### Module - Search on Internet

### Module - Text Extraction

### Module - Document classification

### Module - Database

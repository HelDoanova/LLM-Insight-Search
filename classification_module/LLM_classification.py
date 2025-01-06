import os
import logging
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import tiktoken

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("search_log.log", mode='a', encoding='utf-8'),  # Nastavení UTF-8
    ]
)

class OpenAI:

    def __init__(self):
        load_dotenv()
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not self.OPENAI_API_KEY:
            logging.error("API key not found")
            raise ValueError("API key not set!")
        
        self.max_tokens = 90000
        self.overlap_tokens = 9000
        self.model = "gpt-4o-mini"
    
        # Initialization of OpenAI LLM via LangChain
        self.llm = ChatOpenAI(model=self.model, 
                            api_key=self.OPENAI_API_KEY,
                            temperature=0,
                            max_tokens=300,
                            timeout=None,
                            max_retries=2,)

        self.prompt = """
            Classify the provided document text based on its relevance to the user query, relying solely on the content of the document.

            You will receive two inputs:
            1. **User query**: A short text that describes what the user is looking for, typically in the form of a question or description containing keywords.
            2. **Document text**: The entire document in Markdown format, which may include references or sources within the text.

            Your task:
            1. Compare the document text with the user query and determine its relevance based solely on the information contained in the document.
            2. Summarize the document's content (maximum 30 tokens).
            3. Provide a brief explanation for your classification (maximum 30 tokens).
            4. Classify the document into one of the following categories:
            - **Relevant**: The document directly addresses the user query and provides useful information related to it.
            - **Irrelevant**: The document does not address the user query or contains only unrelated information.

            # Steps
            1. Analyze the user query to understand its intent and main topic.
            2. Examine the document text carefully to determine whether it contains relevant and contextually correct information related to the user query.
            3. Summarize the document's content to provide context for the classification.
            4. Write a concise explanation for the classification.
            5. Classify the document into the appropriate category based on the comparison.

            # Output Format
            The output should be in JSON format with the following structure:
            {
            "classification": "Relevant/Irrelevant",
            "explanation": "Brief explanation (max 30 tokens)",
            "summary": "Summary of document content (max 30 tokens)"
            }


            # Examples
            **Example 1:**
            - **Input:**
            - User query: "What are the benefits of renewable energy?"
            - Document text: "Renewable energy sources like solar and wind provide sustainable power. They reduce carbon emissions and lower energy costs."
            - **Output:**
            {
            "classification": "Relevant",
            "explanation": "Discusses benefits of renewable energy.",
            "summary": "Explains renewable energy sources and its advantages."
            }


            **Example 2:**
            - **Input:**
            - User query: "How to bake a cake?"
            - Document text: "This document includes various recipes for cookies and pastries."
            - **Output:**
            {
            "classification": "Irrelevant",
            "explanation": "Focuses on cookies and pastries, not cake baking.",
            "summary": "Contains recipes for cookies and pastries."
            }


            **Example 3:**
            - **Input:**
            - User query: "What is the difference between apple and pear?"
            - Document text: "This document is about apples, mentions pears only as fruit"
            - **Output:**
            {
            "classification": "Irrelevant",
            "explanation": "Focuses only on apples, not differences with pears.",
            "summary": "Contains informations about apples."
            }

     
            # Notes
            - Base the classification strictly on the document text without introducing any assumptions or invented information.
            - If the document text is inaccessible or an error occurs or access was denaid, etc., return the following output:
            {
            "classification": "ERROR",
            "explanation": "Error description",
            "summary": "What is document about except the error"
            }
        """

    def split_into_chunks(self, document_text):
        """
        Splits a long text into chunks with overlap.

        :param document_text: The text to split into chunks
        :param max_tokens: The maximum number of tokens per chunk
        :param overlap_tokens: The number of overlapping tokens between chunks
        :param model: The name of the LLM used to determine the appropriate tokenization method for tiktoken
        :return: A list of text chunks
        """
        try:
            encoding = tiktoken.encoding_for_model(self.model)
            tokens = encoding.encode(document_text)
            chunk_size = self.max_tokens
            overlap = self.overlap_tokens

            chunks = []
            start = 0
            while start < len(tokens):
                end = start + chunk_size
                chunk = tokens[start:end]
                chunks.append(encoding.decode(chunk))
                start += chunk_size - overlap  # overlap
            
            return chunks
        except Exception as e:
            logging.error(f"Error in split_into_chunks: {e}")
            return []
   
    def classify_document(self, document_text, user_query):
        """
        Classifies the relevance of a document to a user query by processing the document in chunks and combining the results.

        :param document_text: Document text to classify relevance
        :param user_query: User query for document relevance classification
        :return: A JSON string containing the relevance classification, explanation, and summary of the document
        :note:
        - The document is split into chunks using the `split_into_chunks` method.
        - Single-chunk documents are directly processed for relevance using the LLM.
        - Multi-chunk documents are processed chunk by chunk, with results combined to determine overall relevance.
        """
        try:
            chunks = self.split_into_chunks(document_text)
            logging.info(f"Number of chunks: {len(chunks)}")

            # If the document fits into one chunk
            if len(chunks) == 1:
                chunk = chunks[0]
                # Build report for model (Langchain)
                messages = [
                    ( "system", self.prompt,),
                    ("human", f"User query: {user_query}\n\nDocument text:\n{chunk}",),
                ]

                # Call LLM using LangChain
                response = self.llm.invoke(messages)
                return response.content
            else:
                # For multiple chunks
                chunk_results = []
                for i, chunk in enumerate(chunks, start=1):
                    logging.info(f"Proccessing chunk: {i}")
                    messages = [
                        ("system",self.prompt,),
                        ("human",f"User query: {user_query}\n\nDocument text:\n{chunk}",),
                    ]
                    response = self.llm.invoke(messages)
                    try:
                        response_json = json.loads(response.content)
                        chunk_results.append({
                            "classification": response_json.get("classification", ""),
                            "explanation": response_json.get("explanation", ""),
                            "summary": response_json.get("summary", ""),
                        })
                    except json.JSONDecodeError:
                        logging.error("Error decoding response.content into JSON.")
                        continue

                # Evaluation of the relevance of the entire document
                relevance_priority = ["Irrelevant", "Relevant", "ERROR"]
                # Determine the highest level of relevance
                max_relevance_level = max(chunk_results, key=lambda x: relevance_priority.index(x["classification"]))["classification"]
                # Processing by relevance category
                if max_relevance_level == "Irrelevant" or max_relevance_level == "ERROR":
                    first_irrelevant_chunk = chunk_results[0]
                    combined_explanation = first_irrelevant_chunk["explanation"]
                    summary = first_irrelevant_chunk["summary"]
                else:
                    # Combining information from relevant chunks
                    relevant_chunks = [result for result in chunk_results if result["classification"] == "Relevant"]
                    combined_explanation = " | ".join({chunk["explanation"] for chunk in relevant_chunks})
                    summary = " | ".join({chunk["summary"] for chunk in relevant_chunks if chunk["summary"]})

                return json.dumps({
                    "classification": max_relevance_level,
                    "explanation": combined_explanation,
                    "summary": summary
                },)

        except Exception as e:
            logging.error(f"Error in evaluate_document: {e}")
            return None
        
        
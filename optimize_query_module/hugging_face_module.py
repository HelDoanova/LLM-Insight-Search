from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from huggingface_hub import login
import os 
from dotenv import load_dotenv



class HuggingFaceModule:

    def __init__(self):
        load_dotenv()

        load_dotenv()
        self.HF_API_KEY = os.getenv("HF_API_KEY")
        if not self.HF_API_KEY:
            raise ValueError("API key not set!")


        #self.HF_API_KEY = os.getenv("HF_API_KEY")
        self.repo_id = "meta-llama/Llama-3.2-3B-Instruct" 
        #self.repo_id = "mistralai/Mistral-7B-Instruct-v0.3"  
        #self.repo_id = "meta-llama/Llama-3.2-1B-Instruct"   
        #self.repo_id = "microsoft/Phi-3.5-mini-instruct" 

        login(token=self.HF_API_KEY, add_to_git_credential=True)
        self.llm = HuggingFaceEndpoint(
            repo_id=self.repo_id,
            max_new_tokens=20,
            top_k=10,
            top_p=0.85,
            #typical_p=0.95,
            temperature=0.3,
            repetition_penalty=1.04,
            #callbacks=self.callbacks,
            #streaming=True,
            huggingfacehub_api_token=self.HF_API_KEY,
        )

        prompt = (
            "You are an AI assistant specialized in refining and optimizing user queries to ensure accurate and relevant search results on the internet.\n\n"

            "Instructions:\n"
            "Carefully analyze the user's query and rewrite it in a way that maximizes clarity, relevance, and search engine compatibility. Avoid any unnecessary words or ambiguous terms.\n\n"
            "- Do not answer the user's query.\n"
            "- Return only the optimized query as a single sentence.\n"
            "- Do not provide any explanations, examples, note, or additional information.\n"
            "- DO not return exactly the same query. Always optimize.\n"
            "- The response must contain only the optimized query and nothing else.\n"
            "- Any deviation from these instructions is strictly not allowed.\n\n"

            # "Examples:\n"
            # "User Query: What are the best ways to cook Italian paposkytuje pokyny sta using only organic ingredients and including traditional methods like hand-rolled pasta sheets?\n"
            # "Optimized Query: What are best traditional methods for cooking organic Italian pasta\n\n"
            # "User Query: dog anxiety\n"
            # "Optimized Query: Signs of anxiety in dogs\n\n"
            # "User Query: How fix car door, it not close proper way always open when drive?\n"
            # "Optimized Query: How to fix a car door that won't close properly while driving\n\n"

            "Now perform the optimization for the following query:\n"
            "User: {user_input}\n"
            "Optimized Query:"       
        )
        
        self.prompt = PromptTemplate(
            input_variables=["user_input"],
            template=prompt
        )  
        # Connection of prompt and model (pipe operator)
        self.chain = self.prompt | self.llm 

        

    def optimize_query(self, user_input):
        """
        Optimizes a user query 

        :param user_input: The query provided by the user
        :return: The optimized query as returned by the LLM
        :note: Uses a pre-configured chain to process the user query.
        """
        try:
            response = self.chain.invoke({"user_input": user_input})
            return response
        except Exception as e:
            return f"Query optimization error: {e}"


def test():
    """
    Function for testing 
    Allows the user to input queries and receive optimized versions.
    """
    try:
        optimizer = HuggingFaceModule()
        while True:
            user_input = input("Enter your query: ")
            if user_input.lower() == "q":
                print("Exiting the program.")
                break
            optimized_query = optimizer.optimize_query(user_input)
            print(f"Optimized query: {optimized_query}\n")
    except Exception as e:
        print(f"Error running the program: {e}")

if __name__ == "__main__":
    test()
        
    


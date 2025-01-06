import json
import logging
from langchain_community.tools import BraveSearch
import os
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("search_log.log", mode='a', encoding='utf-8'), 
        ]
)
logger = logging.getLogger(__name__)

class BraveSearchEngine:
    def __init__(self, result_count=2):
        load_dotenv()
        self.BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")
        if not self.BRAVE_SEARCH_API_KEY:
            logging.error("API key not found")
            raise ValueError("API key not set!")

        self.brave_search = BraveSearch.from_api_key(
            api_key=self.BRAVE_SEARCH_API_KEY,
            search_kwargs={"count": result_count}
        )

    def extract_links_from_results(self, results):
        """
        Extracts links from search results.

        :param results: list of dictionaries with search results (dictionary: 'link', 'title', 'snippet' )
        :return: list of extracted urls
        """
        if not results:
            logger.error("Unexpected result format. A list of dictionaries is expected.")
            return []

        links = []  
        for result in results:  
            if "link" in result: 
                links.append(result["link"])  

        return links  

    def search(self, query):
        """
        Performs a search via Brave Search

        :param query: search query to execute
        :return: list of extracted URLs from the search results
        """
        try:
            raw_results = self.brave_search.run(query)
            results_json = json.loads(raw_results)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred while searching: {e}")
            return []
        
        links = self.extract_links_from_results(results_json)

        if links:
            return links
        else:
            logger.info("No link was found in the results.")
            return []


def main():
    """
    Test
    """
    engine = BraveSearchEngine(result_count=5)
    user_input = input("Enter your query: ")
    links = engine.search(user_input)
    if links:
        print("Links found:")
        for url in links:
            print(url)
    else:
        print("No links found.")

if __name__ == "__main__":
    main()
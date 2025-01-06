from firecrawl import FirecrawlApp
import os
import logging
from dotenv import load_dotenv
from utils.output_filter import filter_markdown_content, filter_links
import sys
import json

from multiprocessing import Process, Queue

logging.getLogger().handlers.clear()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("search_log.log", mode='a', encoding='utf-8'), 
    ]
)

class FirecrawlExtractor:

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            logging.error("API key not found")
            raise ValueError("API key not set!")
        
        self.app = FirecrawlApp(api_key=self.api_key)

        self.params = {
                "formats": [ "markdown", "links" ],
                "excludeTags": [ 'img', 'iframe', 'header', 'nav', 'footer', 'form' ],           
                "onlyMainContent": True,
                'waitFor': 1000,
                "timeout": 30000,
        }
        self.timeout = 31

        """
        Extrahuje text z jedné URL pomocí FireCrawl API s řízeným timeoutem.

        :param url: URL k extrakci
        :param level: Hloubka prohledávání, ve které se daný odkaz nachází
        :return: Slovník s extrahovaným obsahem nebo None v případě chyby
        """

    def extract_text_from_url(self, url, level):
        """
        Extracts text content from a given URL while handling potential errors and timeouts.

        :param url: The URL to scrape for content
        :param level: The depth level of the scraping RUL
        :return: A tuple containing:
            - document: A dictionary with extracted content, including:
                - url: The original URL
                - markdown: Filtered markdown content from the webpage
                - links: Filtered list of links extracted from the webpage
                - metadata: Metadata related to the scraping process
                - level: The scraping depth level
            - status_code: The HTTP status code returned by the scraping process, or `None` if an error occurred

        :note:
        - Uses multiprocessing to scrape the URL content in a separate process.(Regularly checks the result queue for the scraping output until the timeout is reached.)
        - Handles various HTTP status codes with appropriate actions:
            - 200: Successful extraction; returns the document
            - 400, 404, 429: Logs warnings and skips the URL
            - 401, 402: Logs critical errors and terminates the program
            - 500-599: Logs server errors and skips the URL
            - 403: Logs access denied warnings and skips the URL
            - Unexpected codes are logged as non-critical warnings
        - Implements a timeout mechanism to terminate unresponsive scraping processes.
        - Filters and processes markdown content and links using helper functions filter_markdown_content and filter_links
        - Logs detailed information, warnings, and errors for debugging and monitoring purposes, because Firecrawl is not pereft despite they are trying
        """
        
        # Queue for sharing results between processes + start a separate process for the scraping task, passing the queue and URL as arguments
        queue = Queue()  
        process = Process(target=self.scrape_task, args=(queue, url))
        process.start()

        try:
            # Periodically checks the queue to see if the result is ready
            scrape_result = None
            status_code = None
            for _ in range(self.timeout):
                if not queue.empty():
                    scrape_result = queue.get()
                    break
                process.join(timeout=1)  

            if scrape_result is None:  # Timeout
                logging.error(f"TIMEOUT reached for URL: {url}. Terminating process.")
                process.terminate()  # Terminates the process
                process.join()
                return None, None

            if "error" in scrape_result:
                logging.error(f"Error during scraping: {scrape_result['error']}")
                return None, None

            status_code = scrape_result.get("metadata", {}).get("statusCode", None)

            if status_code == 200:
                document = {
                    "url": scrape_result.get("metadata", {}).get("url"),
                    "markdown": filter_markdown_content(scrape_result.get("markdown", "")),
                    "links": filter_links(scrape_result.get("links", [])),
                    "metadata": scrape_result.get("metadata"),
                    "level": level
                }
                logging.info(f"Successfully extracted content for URL: {url}")
                return document, status_code
            elif status_code in [400, 404, 429]:
                logging.warning(f"Non-critical error {status_code} for URL: {url}")
                return None, status_code
            elif status_code in [401, 402]:
                logging.critical(f"Critical error {status_code} for URL: {url}. Terminating program...")
                sys.exit(f"Critical error {status_code} encountered for URL: {url}")
            elif 500 <= status_code < 600:
                logging.warning(f"Server error {status_code} for URL: {url}. Skipping...")
                return None, status_code
            elif status_code == 403:
                logging.warning(f"Access denied (403) for URL: {url}. Skipping...")
                return None, status_code
            else:
                logging.warning(f"Unexpected status code {status_code} for URL: {url}. Handling as non-critical.")
                return None, status_code

        except Exception as e:
            logging.error(f"Unexpected error for URL: {url}. Terminating process. Error: {e}")
            process.terminate()  # Process termination on error
            process.join()
            return None, None

    def scrape_task(self, queue, url):
        """
        Scrapes the content of a given URL and puts the result in a queue.

        :param queue: A multiprocessing queue used to share the scraping result with the main process
        :param url: The URL to scrape
        """
        try:
            result = self.app.scrape_url(url, self.params)
            queue.put(result)  # Výsledek vrací do fronty
        except json.JSONDecodeError as e:
            queue.put({"error": f"Invalid JSON format: {e}"})
        except Exception as e:
            queue.put({"error": str(e)})
 



def test_extract_text():
        """Test"""
        logging.info("Starting test for extract_text_from_url...")
        extractor = FirecrawlExtractor()

        test_url = "https://example.com"
        test_level = 1

        try:
            # Call the extraction function
            document, status_code = extractor.extract_text_from_url(test_url, test_level)

            if document:
                print("Document successfully extracted:")
                print(json.dumps(document, indent=2))
            else:
                print(f"Failed to extract document. Status code: {status_code}")
        except Exception as e:
            print(f"An error occurred during the test: {e}")

if __name__ == "__main__":
     test_extract_text()






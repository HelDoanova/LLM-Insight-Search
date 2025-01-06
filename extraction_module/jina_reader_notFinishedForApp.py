import requests
import os
import logging
from dotenv import load_dotenv
import json
import re


# Nastavení logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("search_log.log"),
    ]
)

logger = logging.getLogger(__name__)


class WebContentExtractor:
    def __init__(self):
        load_dotenv()
        self.JINA_API_KEY = os.getenv("JINA_API_KEY")
        self.headers = {
            #'Accept': 'application/json',
            'Authorization': f'Bearer {self.JINA_API_KEY}',
            'X-No-Cache': 'true'
        }
        # Vytvoří složku jina_output, pokud neexistuje
        if not os.path.exists('jina_output'):
            os.makedirs('jina_output')

    def extract_and_save(self, urls, database_handler ):
        for url in urls:
            try:
                # Připraví URL pro Jina AI Reader API
                api_url = f'https://r.jina.ai/{url}'
                response = requests.get(api_url, headers=self.headers)
                if response.status_code == 200:
                    content = response.text

                    data = self.parse_content_for_database(content)
                    database_handler.insert_data(data)

                else:
                    logger.error(f'Error getting content from {url}: {response.status_code}')
            except Exception as e:
                logger.exception(f'Expection proccesing {url}: {e}')


    def parse_content_for_database(self, content):
        try:
            # Rozdělení obsahu na jednotlivé části
            # Použijeme regulární výrazy pro extrakci dat
            title_match = re.search(r'Title:\s*(.*)', content)
            url_match = re.search(r'URL Source:\s*(.*)', content)
            time_match = re.search(r'Published Time:\s*(.*)', content)
            markdown_match = re.search(r'Markdown Content:\s*(.*)', content, re.DOTALL)

            if title_match and url_match and markdown_match:
                title = title_match.group(1).strip()
                source_url = url_match.group(1).strip()
                markdown_content = markdown_match.group(1).strip()

                # Ošetření Published Time
                if time_match:
                    publish_time = time_match.group(1).strip()
                else:
                    publish_time = ''  

                data = {
                    "markdown": markdown_content,
                    "title": title,
                    "sourceURL": source_url,
                    "publishTime": publish_time
                    
                }
                return data
            else:
                logger.error('Error getting all parts of content.')
                return None
        except Exception as e:
            logger.exception(f'Expection parsing content: {e}')
            return None

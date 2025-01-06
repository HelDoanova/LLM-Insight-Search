import os
import json
import logging


logging.getLogger().handlers.clear()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("search_log.log", mode='a', encoding='utf-8'), 
    ]
)


class JsonWriter:
    def __init__(self, output_folder="OUTPUT"):
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)

    def save_overview_to_file(self, total_links, filename_search_query):
        """
        Saves the contents of the total_links dictionary to a JSON file.

        :param total_links: A dictionary containing data about processed links.
        :param filename_search_query: The file name derived from the search query.
        """
        output_file = os.path.join(self.output_folder, f"overview_{filename_search_query}.json")

        try:
            with open(output_file, "w", encoding="utf-8") as file:
                json.dump(total_links, file, indent=4, ensure_ascii=False)
            logging.info(f"Overview saved to: {output_file}")
        except Exception as e:
            logging.error(f"Error saving overview to file: {e}")




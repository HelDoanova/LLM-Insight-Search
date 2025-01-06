from optimize_query_module.hugging_face_module import HuggingFaceModule
from search_module.brave_search_engine import BraveSearchEngine
from extraction_module.firecrawl_extractor_v3 import FirecrawlExtractor
from database_module.mongoDB import MongoDB
from classification_module.LLM_classification import OpenAI
from utils.excel_writer import ExcelWriter
from utils.json_writer import JsonWriter

import os
import json
import time
import logging

from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.text import Text
from rich.spinner import Spinner
from rich.panel import Panel
from rich.rule import Rule

logging.getLogger().handlers.clear()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("search_log.log", mode='a', encoding='utf-8'), 
    ]
)


# BEGIN INTERACTION WITH USER -----------------------------------------------------------------------------------------------
title = """ # LLM Insight Search """
optimize_confirm = Text("Would you like to optimize your query?")
optimize_confirm.stylize("blue")
user_query_text = Text("Enter your query to optimize it")
user_query_text.stylize("blue")
search_query_text = Text("Enter your query to perform search")
search_query_text.stylize("blue")

result_count_text = Text("Enter the number of search results for depth level 0")
result_count_text.stylize("blue")

max_depth_text = Text("What is the maximum depth level you want to search?")
max_depth_text.stylize("blue")
max_scraped_docs_text = Text("What is the maximum number of documents you want to process?")
max_scraped_docs_text.stylize("blue")

console = Console()
title = Markdown(title)
# END INTERACTION WITH USER -----------------------------------------------------------------------------------------------

# BEGIN COMPUTING STATISTICS -----------------------------------------------------------------------------------------------
def count_relevance(total_links):
    relevant_count = sum(1 for data in total_links.values() if data.get("classification", None) == "Relevant")
    irrelevant_count = sum(1 for data in total_links.values() if data.get("classification", None) == "Irrelevant")
    error_count = sum(1 for data in total_links.values() if "ERROR" in data.get("classification", ""))

    # Výpis výsledků
    console.print(f"\n[bold green]Total Relevant URLs:[/] {relevant_count}")
    console.print(f"[bold magenta]Total Irrelevant URLs:[/] {irrelevant_count}")
    console.print(f"[bold red]Total ERROR URLs:[/] {error_count}")
    return relevant_count,irrelevant_count, error_count, 
# END COMPUTING STATISTICS -----------------------------------------------------------------------------------------------

def process_urls(current_urls, extractor, classifier, database_handler, remaining_scraped_urls, level, search_query, excel_writer, json_writer, file_path, total_links, filename_search_query):
    """
    Processes URLs iteratively, performs extraction and relevance classification, and saves the results to a database, Excel and json.

    :param current_urls: List of URLs to process
    :param extractor: Instance of the extraction module
    :param classifier: Instance of the relevance classification module
    :param database_handler: Instance of the database handler
    :param remaining_scraped_urls: Number of remaining URLs to process
    :param level: Depth level
    :param search_query: Query used to classify relevance
    :param excel_writer: Instance of the module for writing to Excel
    :param file_path: Path to the output Excel file
    :param total_links: Dictionary to store all links
    :return: Links for further in-depth analysis, total extraction and classification time
    """
    processed_count = 0
    extraction_time = 0
    classification_time = 0
    next_level_links = []

    for idx, url in enumerate(current_urls, start=1):

        if processed_count >= remaining_scraped_urls:
            break

# EXTRACTION PROCCESS CALLING
        start_time_extraction = time.time()
        with console.status(f"[bold blue] Extracting data from URL {idx}/{len(current_urls)}.[/]", spinner="aesthetic"):
            logging.info(f"Extracting URL: {url} at level {level} - {idx}/{len(current_urls)}")
            document, status_code = extractor.extract_text_from_url(url, level)
            processed_count += 1
        end_time_extraction = time.time()
        extraction_time += (end_time_extraction - start_time_extraction)

        # Check for None
        if document is None and status_code is None:
            logging.warning("INVALID MARKDOWN")
            logging.warning(f"Both document and status_code are None for URL: {url}. Skipping.")
            continue

        if status_code == 200:
            if not document or not document.get("markdown") or document.get("markdown") == "":
                logging.warning("INVALID MARKDOWN")
                logging.warning(f"Document with {url} has empty markdown content. Skipping classification.")
                continue

            start_time_classification = time.time()
            with console.status(f"[bold blue]Classifying document relevance. {idx}/{len(current_urls)}[/]", spinner="aesthetic"):
                logging.info(f"Classifying document: {url} at level {level} - {idx}/{len(current_urls)}")
                relevance_result = classifier.classify_document(document["markdown"], search_query)
            end_time_classification = time.time()
            classification_time += (end_time_classification - start_time_classification)

# CLASSIFICATION PROCCESS CALLING
            try:
                relevance_result = json.loads(relevance_result)
            except json.JSONDecodeError as e:
                logging.warning("INVALID MARKDOWN")
                print(f"Error decoding JSON: {e}")
                #continue
                break
 
            # Adds classification to the document
            document.update({
                "classification": relevance_result.get("classification")
            })

            # Save the results to Excel
            if relevance_result.get("classification") == "Relevant":
                excel_writer.add_urls_to_output_file(
                    file_path, 
                    url
                )

# SAVE THE DOCUMENT TO DATABASE
            database_handler.save_document(document)

            # Store in the total_links dictionary
            total_links[url] = {
                "level": level,
                "classification": relevance_result.get("classification"),
                "explanation": relevance_result.get("explanation"),
                "summary": relevance_result.get("summary")
            }
            # Save the results to JSON
            json_writer.save_overview_to_file(total_links, filename_search_query)

            # Tracking relevant links and checking the maximum number of documents
            if relevance_result.get("classification") == "Relevant": 
                for link in document.get("links", []):
                    if len(next_level_links) >= (remaining_scraped_urls - len(current_urls)):
                        break
                    if link not in total_links:
                        next_level_links.append(link)

        # Error checking
        elif status_code in [400, 404]:
            logging.warning("INVALID URL")
            logging.warning(f"Skipping URL {url} due to status code {status_code}")
        elif status_code == 429:
            logging.warning("INVALID URL")
            with console.status(f"[bold yellow]Rate limit exceeded for URL {url}. Pausing for 61 seconds...[/]", spinner="aesthetic"):
                logging.warning(f"Rate limit exceeded for URL {url}. Pausing for 61 seconds...")
                time.sleep(61)
            continue
        elif 500 <= status_code < 600:  
            logging.warning("INVALID URL")
            logging.warning(f"Server error {status_code} for URL: {url}. Skipping...")
        elif status_code == 403:
            logging.warning("INVALID URL")
            logging.warning(f"Access denied (403) for URL: {url}. Skipping...")
        else:
            logging.warning("INVALID URL")
            logging.warning(f"Unexpected status code {status_code} for URL: {url}. Handling as non-critical.")

        # Limit check - if the number of processed URLs is divisible by 100 without a remainder
        if processed_count % 100 == 0 and status_code != 429:
            with console.status("[bold blue]Rate limit reached. Pausing for 61 seconds...[/]", spinner="aesthetic"):
                time.sleep(61)

    return next_level_links, extraction_time, classification_time


def main():
    console.print(title)
# BLOCK OF BASIC DATA COLLECTION BEGIN
# BEGIN OPTIMIZATION MODULE--------------------------------------------------------------------------------------------------- 
    if Confirm.ask(f"[bold blue]{optimize_confirm}[/]"):
        user_query = Prompt.ask(f"[bold blue]{user_query_text}[/]")
        optimizer = HuggingFaceModule()
        with console.status("[bold blue]Optimizing query with HuggingFace, please wait...[/]", spinner="aesthetic"):
            optimized_query = optimizer.optimize_query(user_query)
        console.print(f"[bold blue]Optimized query:[/][bold green]{optimized_query}[/]")
        search_query = Prompt.ask(f"[bold blue]{search_query_text}[/]")
    else:
        search_query = Prompt.ask(f"[bold blue]{search_query_text}[/]")
# END OPTIMIZATION MODULE--------------------------------------------------------------------------------------------------- 
# BEGIN SERACH MODULE--------------------------------------------------------------------------------------------------- 
    #result_count = IntPrompt.ask(f"[bold blue]{result_count_text}[/]")
    while True:
        result_count = IntPrompt.ask(f"[bold blue]{result_count_text}[/]")
        if 1 <= result_count <= 20:
            break
        else:
            console.print("[bold red]Invalid input. Please enter a number between 1 and 20.[/]")
    search_engine = BraveSearchEngine(result_count=result_count)  
    urls = search_engine.search(search_query)

    urls_text = "\n".join([f"{url}" for url in urls])
    panel = Panel(urls_text, title=f"[blue]URLs found for serach query on depth level 0", title_align="center", border_style="bold blue")
    console.print(panel)
# END SERACH MODULE--------------------------------------------------------------------------------------------------- 
# BLOCK OF BASIC DATA COLLECTION END

# BLOCK OF DEEP-DIVE DATA PROCCESING BEGIN
# BEGIN DATABASE,EXTRACTION,CLASSIFICATION MODULE -----------------------------------------------------------------
# OUTPUTS
    json_writer = JsonWriter()
    excel_writer = ExcelWriter()
    filename_search_query = excel_writer.modify_serach_query_for_filename(search_query)
    excel_writer.create_output_file_with_search_query(search_query, filename_search_query)
    file_path = os.path.join("OUTPUT", f"{filename_search_query}.xlsx")

# EXTRACTION MODULE
    extractor = FirecrawlExtractor()    
    
# DATABASE MODULE 
    database_handler = MongoDB(database_name="default_db", collection_name=filename_search_query)   # MODUL 4: Database
    console.print(Rule("[bold blue]Available Databases and Collections[/]", style="magenta"))
    database_handler.show_database()
    database_name_new = Prompt.ask("[bold blue]Enter the name of the database you want to use (existing or new). For default press Enter[/]", default="default_db")
    collection_name_new = Prompt.ask("[bold blue]If the collection already exist in selected database, enter a new name. For default press Enter[/]", default=filename_search_query)
    database_handler.set_database(database_name_new)
    database_handler.set_collection(collection_name_new)

# CLASSIFICATION MODULE
    classifier = OpenAI()                                                            
    console.print(Rule("[bold blue]Extraxtion Setting[/]", style="magenta"))
    max_depth  = IntPrompt.ask(f"[bold blue]{max_depth_text}[/]")
    max_scraped_docs = IntPrompt.ask(f"[bold blue]{max_scraped_docs_text}[/]")

    # Set parameters for urls processing
    level = 0
    next_level_links = []
    total_links = {}
    total_extraction_time = 0  
    total_classification_time = 0  
    total_scraped_count = 0
    remaining_scraped_urls = 0

    # Create a file to save the results
    filename_search_query = excel_writer.modify_serach_query_for_filename(search_query)
    excel_writer.create_output_file_with_search_query(search_query, filename_search_query)
    file_path = os.path.join("OUTPUT", f"{filename_search_query}.xlsx")
    total_links["search"] = {"search_query": search_query}
    json_writer.save_overview_to_file(total_links, filename_search_query)


    # Stop condition: The set maximum search depth is reached.
    for level in range(max_depth + 1):
        # Stop condition: The specified maximum number of documents is processed.
        if total_scraped_count >= max_scraped_docs:
            console.print(f"[bold yellow]Maximum number of processed documents ({max_scraped_docs}) reached. Stopping iteration.[/]")
            break

        console.print(Rule(f"[bold blue]Start processing Depth Level {level} ...[/]", style="magenta"))
        
        # Select the URLs for the current level
        current_urls = urls if level == 0 else next_level_links
        next_level_links = []  # Cleanup for extra depth

        # Stop condition: There are no more links available to process at the next (current) level.
        if not current_urls:
            console.print(f"[bold yellow]No URLs found at Level {level}. Terminating search.[/]")
            break

        # Remaining number of URLs to process
        remaining_scraped_urls = max_scraped_docs - total_scraped_count

        # Number of URLs that will actually be processed
        urls_to_process = min(len(current_urls), remaining_scraped_urls)
        console.print(f"[bold blue]URLs to be processed at Depth Level {level}:[/] {urls_to_process}")


# ITERATIVE PROCESS OF PROCESSING URLs FOR SINGLE DEPTHS
        level_next_links, level_extraction_time, level_classification_time = process_urls(
            current_urls,
            extractor,
            classifier,
            database_handler,
            remaining_scraped_urls,
            level,
            search_query,
            excel_writer,
            json_writer,
            file_path,
            total_links,
            filename_search_query
        )

        # Update statistics
        total_extraction_time += level_extraction_time
        total_classification_time += level_classification_time
        total_scraped_count += len(current_urls)
        next_level_links.extend(level_next_links)

        # Pause between levels if next_level_links is not empty  
        if next_level_links and level < max_depth:
            console.print(f"[bold blue]Processing documents on Depth Level {level} DONE.[/]")
            with console.status("[bold blue]Waiting for 61 seconds before proceeding to the next depth level. Please wait... [/]", spinner="aesthetic"):
                time.sleep(61)

# END DATABASE,EXTRACTION,CLASSIFICATION MODULE -----------------------------------------------------------------
# BLOCK OF DEEP-DIVE DATA PROCCESING END

    # APP END
    console.print(Rule("[bold magenta]APP END[/]", style="blue"))

    relevant_count,irrelevant_count, error_count = count_relevance(total_links)
    invalid_count = max_scraped_docs - (len(total_links)-1)
    console.print(f"[bold red]Total invalid URLs:[/] {invalid_count}")

    total_links["overview"] = {
    "relevant_count": relevant_count,
    "irrelevant_count": irrelevant_count,
    "error_count": error_count,
    "invalid_count": invalid_count,
    #"total_extraction_time_seconds": total_extraction_time,
    #"total_classification_time_seconds": total_classification_time
    }
    json_writer.save_overview_to_file(total_links, filename_search_query)
    
    #console.print(Rule("[bold magenta]Extraction and Classification Time[/]", style="blue"))
    #console.print(f"[bold green]Total extraction time: {total_extraction_time:.2f} seconds[/]")
    #console.print(f"[bold green]Total classification time: {total_classification_time:.2f} seconds[/]")
    
    
if __name__ == "__main__":
    main()


import re
from urllib.parse import urlparse, parse_qs
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("search_log.log", mode='a', encoding='utf-8'), 
    ]
)


def filter_markdown_content(markdown):
    """
    Removes references or undesired sections from the markdown content

    :param markdown: Text in markdown format
    :return: Modified markdown content without references
    """
    try:
        # Search for sections with references using common header keywords
        pattern = r"#+\s*(References|Citations|Bibliography|Sources|Literature|External links)"
        match = re.search(pattern, markdown, re.IGNORECASE)

        if match:
            reference_header = match.group(0)
            content, _ = markdown.split(f"{reference_header}", maxsplit=1)
            return content.strip()

        return markdown

    except Exception as e:
        logging.error(f"Error during reference removal : {e}")
        print(f"Error during reference removal: {e}")
        # ValueError(f"Error during reference removal: {e}")
        return None 
    
def filter_links(links):
    """
    Filters undesired links from a provided list and processes Google Scholar links

    :param links: List of URLs to filter
    :return: A list of filtered URLs
    """
    try:
        email_pattern = r"mailto:"
        youtube_pattern = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/"
        void_pattern = r"^javascript:void\(0\);?$"
        wikimedia_pattern = r"(https?://)?(www\.)?(donate\.wikimedia\.org|foundation\.wikimedia\.org)/.*"
        quora_pattern = r"(https?://)?(www\.)?quora\.com/.*"
        pinterest_pattern = r"(https?://)?(www\.)?pinterest\.com/.*"
        facebook_pattern = r"(https?://)?(www\.)?facebook\.com/.*"
        instagram_pattern = r"(https?://)?(www\.)?instagram\.com/.*"
        twitter_pattern = r"(https?://)?(www\.)?twitter\.com/.*"
        image_pattern = r"\.(jpg|jpeg|png|gif|bmp|webp|svg|tiff|tif|ico)(\?.*)?$"
        google_scholar_pattern = r"(https?://)?(scholar\.google\.com)/scholar_lookup.*"

        cleaned_links = []
        for link in links:
            # Filter common undesired links
            if (
                not re.match(email_pattern, link)
                and not re.match(youtube_pattern, link)
                and not re.match(void_pattern, link)
                and not re.match(wikimedia_pattern, link)
                and not re.match(quora_pattern, link)
                and not re.match(pinterest_pattern, link)
                and not re.match(facebook_pattern, link)
                and not re.match(instagram_pattern, link)
                and not re.match(twitter_pattern, link)
                and not re.search(image_pattern, link, re.IGNORECASE)
            ):
                # Process Google Scholar links
                if re.match(google_scholar_pattern, link):
                    parsed_url = urlparse(link)
                    query_params = parse_qs(parsed_url.query)

                     # Attempt to extract DOI or retain the original link
                    doi = query_params.get("doi", [None])[0]
                    if doi:
                        direct_url = f"https://doi.org/{doi}"
                        cleaned_links.append(direct_url)
                    else:
                        cleaned_links.append(link)
                else:
                    cleaned_links.append(link)

        return cleaned_links

    except Exception as e:
        logging.error(f"Error during links filtering: {e}")
        print(f"Error during links filtering: {e}")
        #raise ValueError(f"Error during links filtering: {e}")
        return None
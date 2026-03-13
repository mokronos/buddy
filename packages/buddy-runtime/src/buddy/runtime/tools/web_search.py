import json
import logging
from dataclasses import dataclass

import cloudscraper
import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException, Timeout

# your searxng instance
url = "http://localhost:8888/search"
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    title: str
    url: str


def web_search(query: str) -> str:
    params = {"q": query, "format": "json"}

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (compatible; MyBot/1.0)"},
        )
    except RequestsConnectionError:
        return (
            "Web search is currently unavailable because the local SearXNG service is unreachable. "
            "I cannot perform web searches right now."
        )
    except Timeout:
        return (
            "Web search is currently unavailable because the local SearXNG service timed out. "
            "I cannot perform web searches right now."
        )
    except RequestException:
        return (
            "Web search is currently unavailable because the local SearXNG request failed. "
            "I cannot perform web searches right now."
        )

    if not response.ok:
        return (
            f"Web search is currently unavailable because SearXNG returned HTTP {response.status_code}. "
            "I cannot perform web searches right now."
        )

    try:
        data = response.json()
    except ValueError:
        return (
            "Web search is currently unavailable because SearXNG returned an invalid response. "
            "I cannot perform web searches right now."
        )

    results = []
    # results are in data["results"]
    for r in data.get("results", [])[:5]:
        results.append({
            "title": r.get("title", "No title"),
            "url": r.get("url", ""),
        })
    return json.dumps(results)


def fetch_web_page(url: str) -> str:
    """
    Fetches the HTML content of a web page.
    Does not work for direct urls to pdfs, images, etc.!
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    }
    if not url.strip().startswith(("http://", "https://")):
        return "Invalid URL. Provide a full URL starting with http:// or https://."

    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(url, headers=headers, timeout=15)
    except Timeout:
        return "Fetching the page timed out. Try a different URL or retry later."
    except RequestException:
        logger.exception("fetch_web_page request failed", extra={"url": url})
        return "Could not fetch the page. Verify the URL is reachable and try again."

    if response.ok:
        soup = BeautifulSoup(response.text, "html.parser")
        # for tag in soup(["script", "style", "noscript"]):
        #     tag.extract()
        # cleaned_html = soup.prettify()
        data = soup.get_text(separator="\n", strip=True)
        metadata = f"---\nurl: {url}\n---\n"
        result = metadata + data
        return result
    else:
        return f"Page fetch failed with HTTP {response.status_code}. Try a different URL or retry later."


if __name__ == "__main__":
    res = web_search("kai cenat linkin park")
    print(res)

    res = json.loads(res)

    res1 = res[0]

    print(f"title: {res1['title']}, url: {res1['url']}")

    res2 = fetch_web_page(res1["url"])
    print(res2)

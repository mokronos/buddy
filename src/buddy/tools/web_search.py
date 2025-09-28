import json
from dataclasses import dataclass

import cloudscraper
import requests
from bs4 import BeautifulSoup

# your searxng instance
url = "http://localhost:8888/search"


@dataclass
class SearchResult:
    title: str
    url: str


def web_search(query: str) -> str:
    params = {"q": query, "format": "json"}

    response = requests.get(url, params=params)

    if response.ok:
        data = response.json()

        results = []

        # results are in data["results"]
        for r in data["results"][:5]:
            results.append({"title": r["title"], "url": r["url"]})
        return json.dumps(results)
    else:
        return f"Error: {response.status_code} | {response.text}"


def fetch_web_page(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    }
    scraper = cloudscraper.create_scraper()
    response = scraper.get(url, headers=headers)

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
        return f"Error: {response.status_code} | {response.text}"


if __name__ == "__main__":
    res = web_search("kai cenat linkin park")
    print(res)

    res = json.loads(res)

    res1 = res[0]

    print(f"title: {res1['title']}, url: {res1['url']}")

    res2 = fetch_web_page(res1["url"])
    print(res2)

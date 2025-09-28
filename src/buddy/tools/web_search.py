import requests

# your searxng instance
url = "http://localhost:8888/search"


def web_search(query: str) -> str:
    params = {"q": query, "format": "json"}

    response = requests.get(url, params=params)

    if response.ok:
        data = response.json()

        # results are in data["results"]
        for r in data["results"][:5]:
            print(r["title"], "->", r["url"])
    else:
        print("Error:", response.status_code, response.text)


if __name__ == "__main__":
    web_search("kai cenat linkin park")

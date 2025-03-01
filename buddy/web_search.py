from typing import Annotated, Any
from langchain_core.tools import BaseTool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from dotenv import load_dotenv

import requests
from langgraph.graph.state import Command
from langgraph.prebuilt import InjectedState
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

from pydantic import BaseModel, Field

load_dotenv()

class WebSearchInput(BaseModel):
    query: str = Field(description="Query to search for")
    tool_call_id: Annotated[str, InjectedToolCallId] = ""
    docs: Annotated[Any, InjectedState] = []



class WebSearch(BaseTool):
    name: str = "web_search"
    description: str = "Searches the web for information."
    args_schema: type[WebSearchInput] = WebSearchInput

    search_engine: str = ""
    wrapper: DuckDuckGoSearchAPIWrapper = DuckDuckGoSearchAPIWrapper()
    search: DuckDuckGoSearchResults = DuckDuckGoSearchResults()
    num_results: int = 5
    region: str = "en_us"
    full_page: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_engine = self.search_engine
        self.wrapper = DuckDuckGoSearchAPIWrapper(region=self.region)
        self.search = DuckDuckGoSearchResults(
            api_wrapper=self.wrapper, num_results=self.num_results, output_format="list"
        )

    def format_docs(self, docs: list) -> str:

        str_docs = []

        for doc in docs:
            content = ""
            if self.full_page:
                content = doc["site_content"]
            s = f"""
                ---
                Title: {doc["title"]}
                Link: {doc["link"]}
                Snippet: {doc["snippet"]}
                ---
                {content}
            """
            str_docs.append(s)

        return "\n\n---\n\n".join(str_docs)


    def get_site(self, url: str) -> str:
        reader_url = "https://r.jina.ai/"

        resp = requests.get(f"{reader_url}{url}")

        return resp.text

    def _run(
        self,
        query: str = Field(description="Query to search for"),
        tool_call_id: Annotated[str, InjectedToolCallId] = "",
        docs: Annotated[Any, InjectedState] = [],
    ) -> Command:

        print("Calling web search tool")
        if hasattr(docs, "docs"):
            existing_docs = docs.docs
        else:
            existing_docs = []

        # if hasattr(state, "docs"):
        #     existing_docs = state.docs
        #     print(f"Found {existing_docs} docs in state")
        # else:
        #     existing_docs = []
        #     print("No docs found in state")

        results = self.search.run(query)

        if self.full_page:
            for d in results:
                d["site_content"] = get_site(d["link"])

        if hasattr(docs, "docs"):
            return Command(
                update={
                    "docs": existing_docs + results,
                    "messages": [
                        ToolMessage(
                            self.format_docs(results),
                            tool_call_id=tool_call_id,
                        )
                    ],
                }
            )
        
        else:
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            self.format_docs(results),
                            tool_call_id=tool_call_id,
                        )
                    ],
                }
            )





if __name__ == "__main__":
    from rich.console import Console
    from rich.markdown import Markdown

    console = Console()

    search = WebSearch(num_results=1, full_page=False)

    resp = search.invoke(
        {
            "query": "What is the capital of France?",
            "tool_call_id": "091205305faef",
        }
    )

    content = resp.update["messages"][-1].content

    console.print(Markdown(content))

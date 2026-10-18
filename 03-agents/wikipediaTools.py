import json
import requests

class WikipediaTools:
    """
    Provides search for keyword and pages in wikipedia using wikipedia API.
    """
    def __init__(self):
        pass

    def get_page(self,pagetitle:str)->str:
        """
        Search the index for results matching a query and highlight them.
        Args:
            pagetitle (str): The search query to look up wikipedia pages.
            Returns:
            str: the content of the page.
        """
        response= requests.get(
            f"https://en.wikipedia.org/w/rest.php/v1/page/{pagetitle}",
            headers={"User-Agent": "ai-engineering-buildcamp-homework/1.0 (your-email@example.com)"},
        )
        response.raise_for_status()
        return response.json()["source"]

    def search_wikipedia(self,query:str)->list[dict]:
        """
            Search wikipedia for results matching a query.
            Args:
                query (str): The search query to look up wikipedia.
                Returns:
                list[dict]: a list of search result objects .
        """
        response=requests.get(
            "https://en.wikipedia.org/w/rest.php/v1/search/page",
            params={"q": query, "limit": 5},
            headers={"User-Agent": "ai-engineering-buildcamp-homework/1.0 (your-email@example.com)"},
        )
        response.raise_for_status()
        return response.json()["pages"]
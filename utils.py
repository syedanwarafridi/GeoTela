from langchain_tavily import TavilySearch
import logging
from typing import Any, Dict, Union, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TAVILY_API_KEY = "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"

def tavily_search(query: str, max_results: int = 1) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    try:
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string.")
        if not isinstance(max_results, int) or max_results <= 0:
            raise ValueError("max_results must be a positive integer.")

        tavily_tool = TavilySearch(
            max_results=max_results,
            tavily_api_key=TAVILY_API_KEY,
            name="tavily_search_tool"
        )

        results = tavily_tool.invoke(query)
        logger.info(f"Tavily search successful for query: '{query}'")

        return results

    except ValueError as ve:
        logger.error(f"Validation error: {ve}")
        return {"error": str(ve)}

    except Exception as e:
        logger.exception(f"An error occurred during Tavily search for query '{query}': {e}")
        return {"error": "An unexpected error occurred while performing the search."}

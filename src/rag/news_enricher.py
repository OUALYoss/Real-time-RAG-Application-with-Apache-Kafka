import requests
import logging
import re
from typing import List, Dict

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"


class NewsEnricher:
    """Enriches disaster event queries with relevant news articles from GDELT"""

    def __init__(self, max_articles: int = 3):
        self.max_articles = max_articles

    def _extract_keywords(self, query: str, events: list) -> set:
        """Extract disaster-related keywords from query and events"""
        keywords = set()

        # Extract from query
        disaster_terms = [
            "earthquake",
            "flood",
            "wildfire",
            "cyclone",
            "hurricane",
            "tornado",
            "tsunami",
            "volcano",
            "landslide",
            "drought",
        ]
        query_lower = query.lower()
        for term in disaster_terms:
            if term in query_lower:
                keywords.add(term)

        # Extract locations from query (simple extraction)
        # Look for capitalized words that might be places
        words = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", query)
        keywords.update(words[:3])  # Limit to 3 location keywords

        # Extract from event metadata
        for event in events[:3]:  # Check first 3 events
            metadata = event.get("metadata", {})
            if metadata.get("place"):
                # Extract location from place string
                place_parts = metadata["place"].split(",")
                if place_parts:
                    keywords.add(place_parts[-1].strip())

            event_type = metadata.get("event_type", "")
            if event_type and event_type != "unknown":
                keywords.add(event_type)

        return keywords

    def enrich(self, query: str, events: list) -> Dict:
        """
        Query GDELT for news articles related to the disaster query

        Args:
            query: User's question
            events: Retrieved disaster events from vector store

        Returns:
            Dict with 'articles' list and 'keywords' used
        """
        if not events:
            return {"articles": [], "keywords": []}

        # Extract relevant keywords
        keywords = self._extract_keywords(query, events)

        if not keywords:
            return {"articles": [], "keywords": []}

        # Build GDELT query
        gdelt_query = " OR ".join(keywords) + " sourcelang:english"

        params = {
            "query": gdelt_query,
            "mode": "ArtList",
            "format": "json",
            "timespan": "24h",  # Last 24 hours for relevance
            "maxrecords": str(self.max_articles * 2),  # Get extras to filter
            "sort": "DateDesc",
        }

        try:
            resp = requests.get(GDELT_DOC_API, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()

            articles = data.get("articles", [])[: self.max_articles]

            # Format for consumption
            formatted_articles = []
            for article in articles:
                formatted_articles.append(
                    {
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "domain": article.get("domain", ""),
                        "seendate": article.get("seendate", ""),
                    }
                )

            logging.info(
                f"GDELT enrichment: {len(formatted_articles)} articles for keywords: {keywords}"
            )

            return {"articles": formatted_articles, "keywords": list(keywords)}

        except Exception as e:
            logging.error(f"Error enriching with GDELT: {e}")
            return {"articles": [], "keywords": list(keywords)}

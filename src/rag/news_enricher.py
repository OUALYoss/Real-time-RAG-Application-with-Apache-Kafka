import requests
import logging
import re
from typing import List, Dict

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"


class NewsEnricher:
    """Enriches disaster event queries with relevant news articles from GDELT"""

    def __init__(self, max_articles: int = 3):
        self.max_articles = max_articles
        self.disaster_terms = [
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
            "storm",
            "blizzard",
            "heatwave",
            "avalanche",
            "wildfire",
            "fire",
            "lava",
            "tremor",
            "seismic",
            "typhoon",
            "monsoon",
            "evacuation",
            "emergency",
            "alert",
            "disaster",
            "eruption",
            "overflow",
            "damage",
            "casualty",
            "missing",
        ]
        self.excluded_terms = [
            "wedding",
            "marriage",
            "celebrity",
            "museum",
            "tax",
            "bilk",
            "business",
            "economy",
            "sport",
            "football",
            "travel",
            "lifestyle",
            "fashion",
            "cruise",
            "concert",
            "festival",
        ]

    def _extract_keywords(self, query: str, events: list) -> set:
        """Extract disaster-related keywords from query and events"""
        keywords = set()

        query_lower = query.lower()
        for term in self.disaster_terms:
            if term in query_lower:
                keywords.add(term)

        # Better location detection patterns: "in [Place]", "near [Place]", etc.
        location_patterns = [
            r"in\s+([a-zA-Z]{3,}(?:\s+[a-zA-Z]{3,})*)",
            r"near\s+([a-zA-Z]{3,}(?:\s+[a-zA-Z]{3,})*)",
            r"at\s+([a-zA-Z]{3,}(?:\s+[a-zA-Z]{3,})*)",
            r"([a-zA-Z]{3,}(?:\s+[a-zA-Z]{3,})*)\s+area",
        ]

        for pattern in location_patterns:
            matches = re.finditer(
                pattern, query
            )  # removed IGNORECASE to maintain some specificity
            for match in matches:
                loc = match.group(1).strip()
                if loc.lower() not in self.disaster_terms:
                    keywords.add(loc)

        # Fallback: generalized capitalized words (likely proper nouns/cities)
        # We still keep this for the "Hawaii" (capitalized) case if it's not preceded by "in"
        generic_locations = re.findall(r"\b[A-Z][a-z]{3,}\b", query)
        for loc in generic_locations:
            if loc.lower() not in self.disaster_terms:
                keywords.add(loc)

        # Extract from event metadata (first 2 events for high precision)
        for event in events[:2]:
            metadata = event.get("metadata", {})
            place = metadata.get("place", "")
            if place:
                # Get the last segment (usually country/state) and the first (usually city)
                parts = [p.strip() for p in place.split(",")]
                if parts:
                    keywords.add(parts[0])  # City/Region
                    if len(parts) > 1:
                        keywords.add(parts[-1])  # Country

            e_type = metadata.get("event_type", "")
        # Post-processing: If we found a location but no disaster type,
        # add a generic disaster search term to GDELT to stay on-topic.
        has_disaster_term = any(t in keywords for t in self.disaster_terms)
        locations = {k for k in keywords if k not in self.disaster_terms}

        if locations and not has_disaster_term:
            keywords.add("disaster")
            keywords.add("emergency")

        return {k for k in keywords if len(k) > 2}

    def enrich(self, query: str, events: list) -> Dict:
        """Query GDELT for news articles related to the disaster query"""
        keywords = self._extract_keywords(query, events)
        logging.info(f"Targeting GDELT with keywords: {keywords}")

        if not keywords:
            return {"articles": [], "keywords": []}

        # Build GDELT query logic:
        # Location AND (DisasterTerm1 OR DisasterTerm2 OR ...)
        location_terms = {k for k in keywords if k not in self.disaster_terms}
        targeted_disaster_terms = {k for k in keywords if k in self.disaster_terms}

        if not targeted_disaster_terms:
            # Fallback if no specific disaster identified
            targeted_disaster_terms = {"disaster", "emergency", "alert"}

        def build_group(terms: set) -> str:
            quoted = []
            for t in sorted(list(terms)):
                if " " in t and not (t.startswith('"') and t.endswith('"')):
                    quoted.append(f'"{t}"')
                else:
                    quoted.append(t)

            if len(quoted) > 1:
                return f"({' OR '.join(quoted)})"
            return quoted[0] if quoted else ""

        query_parts = []
        l_group = build_group(location_terms)
        if l_group:
            query_parts.append(l_group)

        d_group = build_group(targeted_disaster_terms)
        if d_group:
            query_parts.append(d_group)

        gdelt_query = f"{' '.join(query_parts)}"
        # Add negative filters to GDELT
        if self.excluded_terms:
            neg_filters = " ".join([f"-{term}" for term in self.excluded_terms])
            gdelt_query = f"{gdelt_query} {neg_filters}"

        gdelt_query = f"{gdelt_query} sourcelang:english"
        logging.info(f"Targeted GDELT Query: {gdelt_query}")

        params = {
            "query": gdelt_query,
            "mode": "artlist",
            "format": "json",
            "timespan": "3d",
            "maxrecords": "20",  # Increase pool for filtering
            "sort": "hybridrel",
        }

        try:
            logging.info(f"Requesting GDELT: {GDELT_DOC_API} with params {params}")
            resp = requests.get(GDELT_DOC_API, params=params, timeout=15)

            if resp.status_code != 200:
                logging.error(
                    f"GDELT API error: {resp.status_code} - {resp.text[:100]}"
                )
                return {"articles": [], "keywords": list(keywords)}

            try:
                data = resp.json()
            except ValueError:
                logging.error(
                    f"GDELT API returned invalid JSON. Raw response: {resp.text[:200]}"
                )
                return {"articles": [], "keywords": list(keywords)}

            raw_articles = data.get("articles", [])

            # Format and deduplicate (by URL)
            formatted_articles = []
            seen_urls = set()

            for article in raw_articles:
                url = article.get("url", "")
                title = article.get("title", "")
                if not url or url in seen_urls:
                    continue

                # RELEVANCE FILTER:
                # 1. Title must not contain excluded terms
                title_lower = title.lower()
                if any(term in title_lower for term in self.excluded_terms):
                    continue

                # 2. Title must contain at least one disaster-related keyword OR a location keyword
                # (This keeps it strictly on-topic)
                has_disaster = any(term in title_lower for term in self.disaster_terms)
                has_location = any(loc.lower() in title_lower for loc in location_terms)

                # Stronger check: must have disaster term AND (location OR general disaster context)
                if not has_disaster:
                    continue

                seen_urls.add(url)
                formatted_articles.append(
                    {
                        "title": title,
                        "url": url,
                        "domain": article.get("domain", ""),
                        "seendate": article.get("seendate", ""),
                    }
                )

                if len(formatted_articles) >= self.max_articles:
                    break

            logging.info(
                f"GDELT success: {len(formatted_articles)} relevant articles retrieved."
            )
            return {"articles": formatted_articles, "keywords": list(keywords)}
        except Exception as e:
            logging.error(f"GDELT connection failed: {e}")
            return {"articles": [], "keywords": list(keywords)}

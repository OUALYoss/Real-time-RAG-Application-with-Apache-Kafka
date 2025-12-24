import logging

from pytrends.request import TrendReq

from .config import TOPICS
from .producer import BaseProducer

logger = logging.getLogger(__name__)


class TrendsProducer(BaseProducer):
    def __init__(self):
        super().__init__(TOPICS["trends"])
        # hl='en-US' (host language), tz=360 (timezone offset)
        # retries=3, backoff_factor=20 to handle rate limiting
        self.pytrends = TrendReq(hl="en-US", tz=360, retries=3, backoff_factor=20)
        self.keywords = ["earthquake", "flood", "wildfire", "tsunami", "hurricane"]

    def fetch_and_send(self):
        """
        Fetches real-time trending searches or interest over time for specific keywords.
        """
        try:
            # 1. Get Real-time Search Trends (Trending now)
            # Note: real_time_trending_searches is limited to certain regions
            trending_searches = self.pytrends.trending_searches(pn="united_states")

            for index, row in trending_searches.iterrows():
                trend_word = row[0]
                # Only send if it matches our disaster context (simple filter)
                if any(k in trend_word.lower() for k in self.keywords):
                    data = {
                        "type": "trending_search",
                        "query": trend_word,
                        "source": "google_trends",
                        "region": "US",
                    }
                    self.send(f"trend_{trend_word}", data)

            # 2. Get Interest Over Time for core keywords
            self.pytrends.build_payload(self.keywords, timeframe="now 1-H", geo="")
            interest_data = self.pytrends.interest_over_time()

            if not interest_data.empty:
                # Get the latest data point
                latest_point = interest_data.iloc[-1]
                for kw in self.keywords:
                    score = int(latest_point[kw])
                    # Only send if there is significant interest (score > 0)
                    if score > 0:
                        data = {
                            "type": "interest_score",
                            "keyword": kw,
                            "score": score,
                            "source": "google_trends",
                            "description": f"Search interest score for {kw} in the last hour",
                        }
                        self.send(f"score_{kw}", data)

        except Exception as e:
            logger.error(f"Error fetching Google Trends: {e}")


if __name__ == "__main__":
    producer = TrendsProducer()
    producer.fetch_and_send()

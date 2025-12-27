from apscheduler.schedulers.blocking import BlockingScheduler

from .config import INTERVALS
from .gdacs_producer import GDACSProducer
from .nasa_firms_producer import FIRMSProducer
from .newsapi_producer import NewsProducer
from .nws_producer import NWSProducer
from .owm_producer import OWMProducer
from .trends_producer import TrendsProducer
from .usgs_producer import USGSProducer


def main():
    producers = {
        "usgs": USGSProducer(),
        "gdacs": GDACSProducer(),
        "nws": NWSProducer(),
        "owm": OWMProducer(),
        "firms": FIRMSProducer(),
        "news": NewsProducer(),
        # "trends": TrendsProducer(),
    }

    scheduler = BlockingScheduler()

    scheduler.add_job(
        producers["usgs"].fetch_and_send, "interval", seconds=INTERVALS["earthquakes"]
    )
    scheduler.add_job(
        producers["gdacs"].fetch_and_send, "interval", seconds=INTERVALS["disasters"]
    )
    scheduler.add_job(
        producers["nws"].fetch_and_send, "interval", seconds=INTERVALS["weather_nws"]
    )
    scheduler.add_job(
        producers["owm"].fetch_and_send, "interval", seconds=INTERVALS["weather_owm"]
    )
    scheduler.add_job(
        producers["firms"].fetch_and_send, "interval", seconds=INTERVALS["wildfires"]
    )
    scheduler.add_job(
        producers["news"].fetch_and_send, "interval", seconds=INTERVALS["news"]
    )
    # scheduler.add_job(
    #     producers["trends"].fetch_and_send, "interval", seconds=INTERVALS["trends"]
    # )

    for p in producers.values():
        try:
            p.fetch_and_send()
        except Exception:
            pass

    scheduler.start()


if __name__ == "__main__":
    main()

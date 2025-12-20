from apscheduler.schedulers.blocking import BlockingScheduler
from .usgs_producer import USGSProducer
from .gdacs_producer import GDACSProducer
from .nws_producer import NWSProducer


def main():
    usgs = USGSProducer()
    gdacs = GDACSProducer()
    nws = NWSProducer()

    scheduler = BlockingScheduler()
    scheduler.add_job(usgs.fetch_and_send, "interval", seconds=60)
    scheduler.add_job(gdacs.fetch_and_send, "interval", seconds=300)
    scheduler.add_job(nws.fetch_and_send, "interval", seconds=120)

    print("Starting producers...")
    for p in [usgs, gdacs, nws]:
        try:
            p.fetch_and_send()
        except Exception as e:
            print(f"Error: {e}")

    scheduler.start()


if __name__ == "__main__":
    main()

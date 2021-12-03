import os, logging, json, io, gc
from dotenv import load_dotenv
from gdrive import Google_Drive
from utils import get_logger, timeit
from spider import Crawl
from pipe import Pipe

load_dotenv()
get_logger()

ACCOUNT_SECRETS = os.environ.get('ACCOUNT_SECRETS')
PARENT_FOLDER_ID = os.environ.get('DATA_FOLDER_ID')


@timeit
def main(url, start=0, end=-1):
    Google_Drive.init(ACCOUNT_SECRETS, PARENT_FOLDER_ID)
    logger = logging.getLogger("crawler.main")

    logger.info(f"Started crawling: {url}")

    title, res = Crawl.extract_index(url)
    length = len(res)
    logger.info(f"Title: {title} ({start} - {end})")

    Google_Drive.PARENT_FOLDER_ID = Google_Drive.create_folder(
        title, Google_Drive.PARENT_FOLDER_ID)

    pipe = Pipe([
        Crawl.extract_chapter_urls,
        Pipe.customize(start=start, end=end)(Crawl.custom_chapter_range),
        Crawl.fetch_image_urls,
        Crawl.upload_images_drive,
    ])

    out = pipe(res)
    chapter_meta = json.dumps(out, indent=6)
    chapter_meta = io.BytesIO(chapter_meta.encode())

    Google_Drive.create_file(
        "metadata.json",
        Google_Drive.PARENT_FOLDER_ID,
        chapter_meta,
        "application/json",
    )

    with open(f"metadata/{title}.json", "w") as f:
        json.dump(out, f, indent=6)

    gc.collect()
    logger.info("Done crawling!")


if __name__ == "__main__":
    main("https://readmanganato.com/manga-qi951517", 0, 100)

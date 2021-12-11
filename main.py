import gc
import io
import json
import logging
import os

from dotenv import load_dotenv

from gdrive import Google_Drive
from pipe import Pipe
from spider import Crawl
from utils import get_logger, timeit

load_dotenv()
get_logger()

ACCOUNT_SECRETS = os.environ.get('ACCOUNT_SECRETS')
PARENT_FOLDER_ID = os.environ.get('DATA_FOLDER_ID')
METADATA_JSON = os.environ.get('METADATA_JSON')


@timeit
def main(url, start=0, end=-1, _type="manga"):
    Google_Drive.init(ACCOUNT_SECRETS, PARENT_FOLDER_ID)
    logger = logging.getLogger("crawler.main")

    logger.info(f"Started crawling: {url}")

    title, res = Crawl.extract_index(url)

    end = len(res) if end == -1 else end
    logger.info(f"Title: {title} ({start} - {end})")

    Google_Drive.PARENT_FOLDER_ID = Google_Drive.create_folder(
        f"{title} ({start} - {end})",
        Google_Drive.PARENT_FOLDER_ID,
    )

    logger.debug(
        f"Created drive folder --> folder id: {Google_Drive.PARENT_FOLDER_ID}")

    pipe = Pipe([
        Crawl.extract_chapter_urls,
        Pipe.customize(start=start, end=end)(Crawl.custom_chapter_range),
        Crawl.fetch_image_urls,
        Crawl.upload_images_drive,
        Crawl.clean_res,
    ])

    out = pipe(res)

    out = {
        "title": f"{title} ({start} - {end})",
        "num_chapters": len(out),
        "type": _type,
        "chapters": out,
    }

    chapter_meta = json.dumps(out, indent=6)
    chapter_meta = io.BytesIO(chapter_meta.encode())

    file_id = Google_Drive.create_file(
        "metadata.json",
        Google_Drive.PARENT_FOLDER_ID,
        chapter_meta,
        "application/json",
    )
    logger.debug(f"Created metadata drive file --> file id: {file_id}")
    logger.info(f"Uploaded metadata of manga")

    metadata = Google_Drive.download_json_file(METADATA_JSON)
    metadata[file_id] = f"{title} ({start} - {end})"
    metadata = json.dumps(metadata, indent=6)
    Google_Drive.update_json_file(METADATA_JSON, metadata)

    logger.info(f"Updated global metadata index")

    title = title.replace(" ", "_")
    title = f"{title}_{start}-{end}"

    with open(f"metadata/{title}.json", "w") as f:
        json.dump(out, f, indent=6)

    c = gc.collect()
    Crawl.logger.debug(f"Garbage collector --> collected {c} objects")
    logger.info("Done crawling!")


if __name__ == "__main__":
    main("https://readmanganato.com/manga-dr980474", 0, -1, _type="manhwa")
    # main("https://readmanganato.com/manga-qi951517", 0, 2)

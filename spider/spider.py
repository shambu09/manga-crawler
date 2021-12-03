import asyncio
import gc
import io
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import bs4
import requests
from aiohttp import ClientResponseError, ClientSession
from gdrive import Google_Drive


class Crawl:
    THREADS = 30
    logger = logging.getLogger("crawler.spider.Crawl")
    NUM = None

    @staticmethod
    def extract_index(url):
        bs = bs4.BeautifulSoup(requests.get(url).content, "html.parser")
        title = bs.select("div.story-info-right>h1")[0].text
        res = bs.select("li.a-h>a")
        return title, res

    @staticmethod
    def extract_chapter_urls(a):
        chapter = {"title": a.text, "url": a.get("href")}
        return chapter

    @staticmethod
    def sort_chapters(chapters, wrap="__no_wrap__"):
        chapters.reverse()
        for i in range(len(chapters)):
            chapters[i]["chapter"] = i + 1

        return chapters

    @staticmethod
    def custom_chapter_range(chapters, start, end, wrap="__no_wrap__"):
        chapters = Crawl.sort_chapters(chapters)
        return chapters[start:end]

    @staticmethod
    async def async_fetch(session, url):
        try:
            async with session.get(url, timeout=25) as response:
                resp = await response.read()

        except ClientResponseError as e:
            Crawl.logger.error(e)

        except asyncio.TimeoutError as e:
            Crawl.logger.error("Timeout")

        except Exception as e:
            Crawl.logger.error(e, exc_info=True)

        else:
            return resp

    @staticmethod
    async def async_fetch_all(urls, headers):
        tasks = []

        async with ClientSession(headers=headers) as session:
            for url in urls:
                task = asyncio.ensure_future(Crawl.async_fetch(session, url))
                tasks.append(task)

            responses = await asyncio.gather(*tasks)

        return responses

    @staticmethod
    def fetch_resp(urls, headers=None):
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(Crawl.async_fetch_all(urls, headers))
        loop.run_until_complete(future)
        resp = future.result()
        return resp

    @staticmethod
    def fetch_image_urls(chapters, wrap="__no_wrap__"):
        Crawl.NUM = len(chapters)
        urls = []
        for chapter in chapters:
            urls.append(chapter["url"])

        resp = Crawl.fetch_resp(urls)

        for j in range(len(chapters)):
            bs = bs4.BeautifulSoup(str(resp[j]), "html.parser")
            c = bs.select(".container-chapter-reader>img")
            chapters[j]["images"] = [{
                "title": c[i].get("title"),
                "url": c[i].get("src"),
                "page": i + 1,
            } for i in range(len(c))]

            chapters[j]["pages"] = len(c)

        return chapters

    @staticmethod
    def threaded_upload_image(parent_id, name, res):
        _res = io.BytesIO(res)
        file_id = Google_Drive.create_file(name, parent_id, _res, "image/jpeg")
        _res.close()
        return file_id

    @staticmethod
    def upload_images_drive(chapter):
        urls = []
        for image in chapter["images"]:
            urls.append(image["url"])

        headers = {
            "Referer": "https://mangakakalot.com/",
        }
        resp = Crawl.fetch_resp(urls, headers=headers)

        _id = chapter["chapter"]

        folder_id = Google_Drive.create_folder(f"{_id}",
                                               Google_Drive.PARENT_FOLDER_ID)

        chapter["drive_id"] = folder_id
        chapter["drive_url"] = Google_Drive.get_public_url_folder(folder_id)

        chapter["images_links"] = {}

        with ThreadPoolExecutor(max_workers=Crawl.THREADS) as executor:
            file_ids = list(
                executor.map(
                    lambda x: Crawl.threaded_upload_image(
                        folder_id, f"{x[0] + 1}.jpg", x[1]), enumerate(resp)))

        for i, _id in enumerate(file_ids):
            chapter["images_links"][i +
                                    1] = Google_Drive.get_public_url_file(_id)

        Crawl.logger.info(
            f"Downloaded chapter: {chapter['chapter']}/{Crawl.NUM}")

        gc.collect()
        return chapter

    @staticmethod
    def clean_res(chapter):
        del chapter["images"]
        return chapter


class _Crawl:
    @staticmethod
    def download_images(chapter):
        urls = []
        for image in chapter["images"]:
            urls.append(image["url"])

        headers = {
            "Referer": "https://mangakakalot.com/",
        }
        resp = Crawl.fetch_resp(urls, headers=headers)

        folder_name = "res"
        _id = chapter["chapter"]

        if not os.path.isdir(f"{folder_name}/{_id}"):
            os.mkdir(f"{folder_name}/{_id}")

        for i in range(len(resp)):
            with open(f"{folder_name}/{_id}/{i+1}.jpg", "wb") as f:
                f.write(resp[i])

        logging.info(f"Downloaded chapter: {chapter['chapter']}")
        return chapter

    @staticmethod
    def extract_image_urls(chapter):
        url = chapter["url"]
        bs = bs4.BeautifulSoup(requests.get(url).content, "html.parser")
        c = bs.select(".container-chapter-reader>img")
        chapter["images"] = [{
            "title": c[i].get("title"),
            "url": c[i].get("src"),
            "page": i + 1,
        } for i in range(len(c))]

        chapter["pages"] = len(c)

        return _Crawl.download_images(chapter)

    @staticmethod
    async def upload_image(name, parent_id, res):
        try:
            res = io.BytesIO(res)
            file_id = Google_Drive.create_file(name, parent_id, res,
                                               "image/jpeg")

        except ClientResponseError as e:
            logging.error(e)

        except asyncio.TimeoutError as e:
            logging.error("Timeout")

        except Exception as e:
            logging.error(e, exc_info=True)

        else:
            return file_id

    @staticmethod
    async def upload_images(parent_id, resp):
        tasks = []

        for i in range(len(resp)):
            task = asyncio.ensure_future(
                _Crawl.upload_image(f"{i+1}.jpg", parent_id, resp[i]))
            tasks.append(task)

        file_ids = await asyncio.gather(*tasks)

        return file_ids

    @staticmethod
    def upload(parent_id, resp):
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(_Crawl.upload_images(parent_id, resp))
        loop.run_until_complete(future)
        file_ids = future.result()
        return file_ids

import asyncio
import gc
import io
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import bs4
import requests
from aiohttp import ClientResponseError, ClientSession, TCPConnector
from gdrive import Google_Drive


class Fetch:
    logger = logging.getLogger("crawler.spider.Fetch")
    MAX_TRIES = 3
    SEM = asyncio.Semaphore(25)

    @staticmethod
    async def async_fetch(session, url, _type, tries=0):
        if tries > Fetch.MAX_TRIES:
            raise f"Error: Retry limit exceeded (retry: #{tries - 1})"

        resp = None

        try:
            async with Fetch.SEM:
                Fetch.logger.debug(f"Sem value: {Fetch.SEM._value}")
                async with session.get(url, timeout=20) as response:
                    resp = await response.read()

        except ClientResponseError as e:
            Fetch.logger.error(f"{_type}: {e}")

        except asyncio.TimeoutError as e:
            Fetch.logger.warning(
                f"{_type}: Timeout, Retrying (retry: #{tries})")
            try:
                resp = await Fetch.async_fetch(session, url, _type, tries + 1)
            except Exception as e:
                Fetch.logger.error(f"{_type}: Retry Failed --> {e}")
            else:
                Fetch.logger.info(
                    f"{_type}: Retry Successful (retry: #{tries})")
                return resp

        except Exception as e:
            Fetch.logger.error(f"{_type}: {e}", exc_info=True)

        return resp

    @staticmethod
    async def async_fetch_all(urls, headers, _type):
        tasks = []

        connector = TCPConnector(force_close=True)
        async with ClientSession(headers=headers, connector=connector) as session:
            for url in urls:
                task = asyncio.ensure_future(
                    Fetch.async_fetch(session, url, _type))
                tasks.append(task)

            responses = await asyncio.gather(*tasks)

        return responses

    @staticmethod
    def fetch_resp(urls, headers=None, _type="Content"):
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(
            Fetch.async_fetch_all(urls, headers, _type))
        loop.run_until_complete(future)
        resp = future.result()
        return resp


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
    def fetch_image_urls(chapters, wrap="__no_wrap__"):
        Crawl.NUM = len(chapters)
        urls = []
        for chapter in chapters:
            urls.append(chapter["url"])

        resp = Fetch.fetch_resp(urls, _type="Image Urls")

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

        resp = Fetch.fetch_resp(urls, headers=headers, _type="Image Content")

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

        c = gc.collect()
        Crawl.logger.debug(f"Garbage collector collected {c} objects")
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
        resp = Fetch.fetch_resp(urls, headers=headers)

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

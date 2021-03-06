__author__ = 'Alexey Y Manikin'

import datetime
from classes.command.wget import Wget
from helpers.helpers import *
import shutil
import concurrent.futures
from helpers.helpersCollor import BColor


class Downloader(object):

    @staticmethod
    def create_data_dir() -> str:
        """
        Создает директорию с текущей датой в download
        :rtype: unicode
        """
        download_path = os.path.abspath(os.path.join(CURRENT_PATH, 'download'))
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        date_string = datetime.date.fromtimestamp(time.time()).isoformat()
        date_path = os.path.abspath(os.path.join(download_path, date_string))
        if not os.path.exists(date_path):
            os.makedirs(date_path)

        return date_path

    @staticmethod
    def download_file(url: str, data_dir: str) -> bool:
        """
        Скачивает файл в указанную директорию
        :type url: unicode
        :type data_dir: unicode
        :rtype: bool
        """

        wget_until = Wget(url, data_dir)
        command = wget_until.get_command()

        p = SubprocessRunner(command=command)
        p.run()
        p.wait(write_output_in_log=False)
        if p.process.returncode != 0:
            BColor.error("wget p.process.returncode = %s" % p.process.returncode)
            return False

        return True

    @staticmethod
    def download(path: str, item: dict):
        """
        :return:
        """
        file_name = item['file_name']
        url = item['url']
        path_file = os.path.abspath(os.path.join(path, file_name))

        BColor.process("Download %s to %s " % (url, path_file))
        shutil.rmtree(path_file, ignore_errors=True)
        Downloader.download_file(url, path_file)
        if os.path.getsize(path_file) == 0:
            BColor.error("Can`t download file %s to %s" % (url, path_file))
            raise Exception("Can`t download file %s to %s" % (url, path_file))

        return os.path.getsize(path_file)

    @staticmethod
    def download_data_for_current_date() -> str:
        """
        Скачивает все необходимы файлы для парсинга

        С http://archive.routeviews.org информацию по fullview, подробно описывает Павел в своем блоге
        http://phpsuxx.blogspot.com/2011/12/full-bgp.html
        http://phpsuxx.blogspot.com/2011/12/libbgpdump-debian-6-squeeze.html

        для остальных зоне можно посмотреть
        http://csa.ee/databases-zone-files/

        :rtype: unicode
        """
        now_date = datetime.date.today()
        delta = datetime.timedelta(days=1)
        now_date = now_date - delta

        files_list = [{'url': 'https://ru-tld.ru/files/RU_Domains_ru-tld.ru.gz', 'file_name': 'ru_domains.gz'},
                      {'url': 'https://ru-tld.ru/files/SU_Domains_ru-tld.ru.gz', 'file_name': 'su_domains.gz'},
                      {'url': 'https://ru-tld.ru/files/RF_Domains_ru-tld.ru.gz', 'file_name': 'rf_domains.gz'},
                      {'url': 'http://archive.routeviews.org/bgpdata/%s/RIBS/rib.%s.0600.bz2'
                              % (now_date.strftime("%Y.%m"), now_date.strftime("%Y%m%d")), 'file_name': 'rib.bz2'}]

        path = Downloader.create_data_dir()

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(files_list)) as executor:
            future_to_download = {executor.submit(Downloader.download,
                                                   path,
                                                   item): item for item in files_list}
            for future in concurrent.futures.as_completed(future_to_download, timeout=1800):
                item = future_to_download[future]
                file_name = item['file_name']
                url = item['url']
                array_data = future.result()
                BColor.ok("Download url %s to %s, size is %i" % (url, file_name, array_data))

        return path

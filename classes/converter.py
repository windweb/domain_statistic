__author__ = 'alexeyymanikin'

import shutil
import re
from classes.command.gunzip import Gunzip
from classes.command.bgpdump import Bgpdump
from helpers.helpers import *
from config.main import *
from helpers.helpersCollor import BColor


class Converter(object):

    def __init__(self, path: str, show_log: bool = True, delete_work_dir: bool = True):
        """
        :type path: unicode
        :type show_log: bool
        :type delete_work_dir: bool
        :return:
        """
        self.path = path
        self.show_log = show_log
        self.work_path = self._create_work_dir()
        self.prefix = PREFIX_LIST_ZONE.keys()
        self.delete_work_dir = delete_work_dir

        for prefix in self.prefix:
            shutil.copy(os.path.join(self.path, prefix+'_domains.gz'), self.work_path)
            path_archive = os.path.join(self.work_path, prefix+"_domains.gz")
            Converter.unzip_file(path_archive)

    def __del__(self):
        """
        Подчисщаем за собой все
        :return:
        """
        if self.delete_work_dir:
            self._remove_work_dir()

    def get_work_path(self) -> str:
        """
        :rtype: unicode
        """
        return self.work_path

    def _create_work_dir(self) -> str:
        """
        Создает директорию с текущей датой в download
        :rtype: unicode
        """
        work_path = os.path.abspath(os.path.join(self.path, 'work'))
        if not os.path.exists(work_path):
            os.makedirs(work_path)

        return work_path

    def _remove_work_dir(self) -> None:
        """
        Подчищаем за собой
        :return:
        """
        if self.work_path:
            shutil.rmtree(self.work_path)

    @staticmethod
    def unzip_file(path_file: str) -> bool:
        """
        :rtype path_file: unicode
        :return:
        """
        gunzip = Gunzip(path_file)
        command = gunzip.get_command()

        p = SubprocessRunner(command=command)
        p.run()
        p.wait(write_output_in_log=False)
        if p.process.returncode != 0:
            BColor.error("unzip p.process.returncode = %s" % p.process.returncode)
            return False

        return True

    def parse_file_rib_file_to(self, path_rib_file: str or None = None, path_to: str or None = None) -> str:
        """
        :rtype: unicode
        """

        if not path_rib_file:
            path_rib_file = os.path.abspath(os.path.join(self.path, 'rib.bz2'))
            path_to = os.path.abspath(os.path.join(self.work_path, 'rib'))

        shutil.rmtree(path_to, ignore_errors=True)
        bgp_dump = Bgpdump(path_rib_file, path_to)
        command = bgp_dump.get_command()

        p = SubprocessRunner(command=command)
        p.run()
        p.wait(write_output_in_log=False)

        return path_to

    def convert_rib_to_net_as(self, path_rib_file: str or bool = False) -> dict:
        """
        # Input rows format:
        # TIME: 12/19/11 08:00:01
        # TYPE: TABLE_DUMP_V2/IPV4_UNICAST
        # PREFIX: 46.4.0.0/16
        # SEQUENCE: 23998
        # FROM: 80.91.255.62 AS1299
        # ORIGINATED: 12/08/11 05:45:51
        # ORIGIN: IGP
        # ASPATH: 1299 13237 24940 24940 24940 24940 24940
        # NEXT_HOP: 80.91.255.62
        # AGGREGATOR: AS24940 213.133.96.18

        :return:
        """

        if not path_rib_file:
            path_rib_file = os.path.abspath(os.path.join(self.work_path, 'rib'))

        re_prefix = re.compile('^PREFIX:\s+(.*?)$')
        re_aspath = re.compile('^ASPATH:\s(.*?)$')
        re_blank = re.compile('^\s+$')

        network_as = {}
        prefix = ''
        as_path = ''

        file_rib_data = open(path_rib_file, 'r')
        line: str = file_rib_data.readline()
        while line:
            symbol = line[0]
            if symbol == 'T' or symbol == 'S' or symbol == 'F' or symbol == 'O' or symbol == 'N':
                line = file_rib_data.readline()
                continue

            if symbol == 'P':
                match = re_prefix.findall(line)
                if match:
                    prefix = match[0]
                    line = file_rib_data.readline()
                    continue

            if symbol == 'A':
                match = re_aspath.findall(line)
                if match:
                    as_path = match[0].split(" ")[-1]
                    line = file_rib_data.readline()
                    continue

            match = re_blank.findall(line)
            if match and prefix != '':
                network_as[prefix] = as_path

            line = file_rib_data.readline()

        file_rib_data.close()
        return network_as

# -*- coding: utf-8 -*-
__author__ = 'alexeyymanikin'

from classes.command.command import Command

DEFAULT_ARGUMENTS = []


class Gunzip(Command):
    """
    Класс для работы с Gunzip
    """

    OPTIONS = {
    }
    ':type : dict'

    def __init__(self, path: str):
        """
        :type url: unicode
        :type path: unicode
        :return:
        """
        super(Gunzip, self).__init__("gunzip")
        self.path = path

    def get_command(self) -> list:
        """
        Вернуть команду запуска mysqldump
        :return: возвращаем команду запуска
        :rtype: list
        """

        return self.binary + ['-f'] + [self.path]

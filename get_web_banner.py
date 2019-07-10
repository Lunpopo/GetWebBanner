#!/usr/bin/env python
# encoding: utf8
from selenium import webdriver
import requests
import os
import threading
import time
from termcolor import colored
import sqlite3
import platform
from argparse import ArgumentParser
import sys
try:
    import queue
except ImportError:
    import Queue as queue


ROOT_PATH = os.getcwd() + "/"
PNG_PATH = ROOT_PATH + 'saved_png/'
HEADERS = {
    'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
}
DATABASE_FILE = "{}{}".format(ROOT_PATH, 'get_web_banner.sqlite')


class ColorFormatter(object):
    def __init__(self, string_in):
        self.str = string_in

    def fatal(self):
        print colored(self.str, 'red')

    def error(self):
        print "[{}] [{}] {}".format(
            colored(time.strftime("%H:%M:%S"), 'cyan'),
            colored("ERROR", 'red'),
            self.str
        )

    def success(self):
        print "[{}] [{}] {}".format(
            colored(time.strftime("%H:%M:%S"), 'cyan'),
            colored("SUCCESS", 'green'),
            self.str
        )

    def info(self):
        print "[{}] [{}] {}".format(
            colored(time.strftime("%H:%M:%S"), 'cyan'),
            colored("INFO", 'white'),
            self.str
        )


def banner():
    print colored("""
      _____      ___          __  _     ____
     / ____|    | \ \        / / | |   |  _ \\
    | |  __  ___| |\ \  /\  / /__| |__ | |_) | __ _ _ __  _ __   ___ _ __
    | | |_ |/ _ \ __\ \/  \/ / _ \ '_ \|  _ < / _` | '_ \| '_ \ / _ \ '__|
    | |__| |  __/ |_ \  /\  /  __/ |_) | |_) | (_| | | | | | | |  __/ |
     \_____|\___|\__| \/  \/ \___|_.__/|____/ \__,_|_| |_|_| |_|\___|_|
    """, 'cyan')


def send_request(cursor, target_url, verbose=False):
    try:
        response = requests.get(target_url, headers=HEADERS, timeout=5)

        if response.status_code in (200, 302, 403):
            sql = "INSERT INTO cached_online_url (url) VALUES ('{}')".format(target_url)
            cursor.execute(sql)

            string = "{} {}, url 为: {}".format(
                colored('#', 'white'),
                colored("命中成功", 'green'),
                colored(target_url, 'magenta')
            )
            ColorFormatter(string).success()

            option = webdriver.FirefoxOptions()
            option.add_argument('--headless')
            # 禁用 GPU 硬件加速，防止出现bug
            option.add_argument('--disable-gpu')
            if platform.system() == 'Darwin':
                driver_path = "{}{}".format(ROOT_PATH, 'geckodriver_mac')
            elif platform.system() == 'Linux':
                driver_path = "{}{}".format(ROOT_PATH, 'geckodriver_linux')
            else:
                raise "暂时没有Windows 的"

            driver = webdriver.Firefox(executable_path=driver_path,
                                       firefox_options=option)

            driver.get(target_url)
            # 最好添加 time.sleep() 避免图片还没下载完, 主程序就退出了
            time.sleep(10)
            png_name = "{}{}".format(ROOT_PATH + 'saved_png/', target_url.split('://')[1] + '.png')
            result = driver.get_screenshot_as_file(png_name)

            if result:
                string = "存活网页的截图保存的位置在: {}, 文件名为: {}".format(
                    colored(PNG_PATH, 'white'),
                    colored(png_name, 'white')
                )

                ColorFormatter(string).success()
        else:
            if verbose:
                string = "{} {}, {} status code 为: {}".format(
                    colored('#', 'white'),
                    "命中成功",
                    target_url,
                    response.status_code
                )

                ColorFormatter(string).error()

    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.TooManyRedirects):
        if verbose:
            string = "{} {}, url 为: {}".format(
                colored('#', 'white'),
                "命中失败",
                target_url
            )
            ColorFormatter(string).error()

    except sqlite3.OperationalError as e:
        if verbose:
            string = "{} {}, url 为: {}".format(
                colored('#', 'white'),
                "命中失败",
                target_url
            )
            ColorFormatter(string).error()

            ColorFormatter(e).error()

    except sqlite3.ProgrammingError as e:
        if verbose:
            string = "{} {}, url 为: {}".format(
                colored('#', 'white'),
                "命中失败",
                target_url
            )
            ColorFormatter(string).error()
            ColorFormatter(e).error()


def init_database():
    # 初始化数据库
    conn = sqlite3.connect(DATABASE_FILE)
    conn.execute(
        'CREATE TABLE IF NOT EXISTS "cached_online_url" ('
        '`id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,'
        '`url` TEXT NOT NULL'
        ')'
    )
    conn = sqlite3.connect(DATABASE_FILE, isolation_level=None, check_same_thread=False, timeout=20)
    cursor = conn.cursor()
    return cursor


def main():
    url = "http://192.168.{}.{}"

    banner()
    opts = CmdLineParser().cmd_parser()

    if not len(sys.argv[1:]):
        ColorFormatter("You failed to provide an option, redirecting to help menu").fatal()
        # 停顿2秒之后再显示 help banner
        time.sleep(2)
        print
        CmdLineParser().cmd_parser(get_help=True)

    else:
        try:
            if opts.section:
                cursor = init_database()

                # 多线程批量打
                for i in range(1, 255):
                    current_url = url.format(opts.section, i)
                    client_thread = threading.Thread(target=send_request, args=(cursor, current_url, opts.verbose,))
                    client_thread.start()

        except KeyboardInterrupt:
            ColorFormatter("user abort scanning").fatal()


class CmdLineParser(ArgumentParser):
    def __init__(self):
        super(CmdLineParser, self).__init__()

    @staticmethod
    def cmd_parser(get_help=False):
        parser = ArgumentParser(prog=sys.argv[0], add_help=False)

        # helper argument
        helper = parser.add_argument_group('helper arguments')
        helper.add_argument('-h', '--help', help='show this help message and exit', action='help')

        # mandatory argument
        mandatory = parser.add_argument_group("mandatory arguments",
                                              "arguments that have to be passed for the program to run")
        mandatory.add_argument("-c", "--section", type=int, dest="section", metavar="INT",
                               help="type a C section IP address, eg: 2, This is simple option to point ip address "
                                    "section, for example: 192.168.2.0/24. This mean that -c or --section option is 2")

        verbose_arg = parser.add_argument_group("verbose arguments",
                                                "whether turn on verbose mode to output more details info")
        verbose_arg.add_argument("-v", "--verbose", action='store_true', dest="verbose", help="toggle verbose mode")

        opts = parser.parse_args()

        if get_help:
            return parser.print_help()
        else:
            return opts

if __name__ == '__main__':
    main()

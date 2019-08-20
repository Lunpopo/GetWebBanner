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
import subprocess
try:
    from urlparse import urlparse
except:
    from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED


ROOT_PATH = os.getcwd()
PNG_PATH = os.path.join(ROOT_PATH, 'saved_png')
GECKODRIVER_LOG_FILE = os.path.join(ROOT_PATH, 'geckodriver.log')
HEADERS = {
    'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
}
DATABASE_FILE = os.path.join(ROOT_PATH, 'GetWebBanner.sqlite')
SPACER = "+" + "-" * 30 + "+"


class ColorFormatter(object):
    def __init__(self, string_in):
        self.str = string_in

    def fatal(self):
        sys.stdout.write(colored(self.str, 'red') + '\r\n')

    def error(self):
        sys.stdout.write("[{}] [{}] {}\r\n".format(
            colored(time.strftime("%H:%M:%S"), 'cyan'),
            colored("ERROR", 'red'),
            self.str
        ))

    def success(self):
        sys.stdout.write("[{}] [{}] {}\r\n".format(
            colored(time.strftime("%H:%M:%S"), 'cyan'),
            colored("SUCCESS", 'green'),
            self.str
        ))

    def info(self):
        sys.stdout.write("[{}] [{}] {}\r\n".format(
            colored(time.strftime("%H:%M:%S"), 'cyan'),
            colored("INFO", 'white'),
            self.str
        ))

    def warning(self):
        sys.stdout.write("[{}] [{}] {}\r\n".format(
            colored(time.strftime("%H:%M:%S"), 'yellow'),
            colored("WARNING", 'white'),
            self.str
        ))


def banner():
    print(colored("""
      _____      ___          __  _     ____
     / ____|    | \ \        / / | |   |  _ \\
    | |  __  ___| |\ \  /\  / /__| |__ | |_) | __ _ _ __  _ __   ___ _ __
    | | |_ |/ _ \ __\ \/  \/ / _ \ '_ \|  _ < / _` | '_ \| '_ \ / _ \ '__|
    | |__| |  __/ |_ \  /\  /  __/ |_) | |_) | (_| | | | | | | |  __/ |
     \_____|\___|\__| \/  \/ \___|_.__/|____/ \__,_|_| |_|_| |_|\___|_|
    """, 'cyan'))


class Request(object):
    def __init__(self):
        self.request_result_list = []

    @staticmethod
    def normalization_url(url, ssl=False):
        if not urlparse(url).scheme and not urlparse(url).netloc:
            if ssl:
                url = "{}{}".format("https://", url)
            else:
                url = "{}{}".format("http://", url)

            return url
        else:
            return url

    def send_request(self, target_url, verbose=False, ssl=False):
        try:
            target_url = self.normalization_url(url=target_url, ssl=ssl)
            response = requests.get(target_url, headers=HEADERS, timeout=5)

            if not str(response.status_code).startswith('4'):
                Database().insert_data('cached_online_url', target_url)

                string = "{}, url 为: {}".format(
                    "命中成功",
                    colored(target_url, 'magenta')
                )
                ColorFormatter(string).success()
                self.request_result_list.append(target_url)

            else:
                # 4xx 的返回码
                if verbose:
                    string = "{}, {} status code 为: {}".format(
                        "命中成功",
                        target_url,
                        response.status_code
                    )

                    ColorFormatter(string).warning()

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.TooManyRedirects):
            if verbose:
                string = "{}, url 为: {}".format(
                    "命中失败",
                    target_url
                )
                ColorFormatter(string).error()

        except sqlite3.OperationalError as e:
            if verbose:
                string = "{}, url 为: {}".format(
                    "命中失败",
                    target_url
                )
                ColorFormatter(string).error()

                ColorFormatter(e).error()

        except sqlite3.ProgrammingError as e:
            if verbose:
                string = "{}, url 为: {}".format(
                    "命中失败",
                    target_url
                )
                ColorFormatter(string).error()
                ColorFormatter(e).error()

    @staticmethod
    def save_picture(urls, thread_number, pic_path=PNG_PATH):
        executor = ThreadPoolExecutor(max_workers=thread_number)

        def __download_screenshot__(target_url):
            option = webdriver.FirefoxOptions()
            option.add_argument('--headless')
            # 禁用 GPU 硬件加速，防止出现bug
            option.add_argument('--disable-gpu')
            if platform.system() == 'Darwin':
                driver_path = os.path.join(ROOT_PATH, 'geckodriver_mac')
            elif platform.system() == 'Linux':
                driver_path = os.path.join(ROOT_PATH, 'geckodriver_linux')
            else:
                raise "暂时没有 Windows 的"

            driver = webdriver.Firefox(executable_path=driver_path, options=option)

            driver.get(target_url)
            # 最好添加 time.sleep() 避免图片还没下载完, 主程序就退出了
            time.sleep(10)

            # 检查是否有 saved_png 文件夹
            if not os.path.exists(PNG_PATH):
                try:
                    os.makedirs(PNG_PATH)
                except:
                    pass

            png_name = "{}.{}".format(target_url.split('://')[1], 'png')
            save_png_path = os.path.join(pic_path, png_name)
            result = driver.get_screenshot_as_file(save_png_path)

            if result:
                string = "存活网页的截图保存的位置在: {}, 文件名为: {}".format(
                    colored("{}{}".format(pic_path, '/'), 'white'),
                    colored(png_name, 'white')
                )

                ColorFormatter(string).success()

        all_task = [executor.submit(__download_screenshot__, url) for url in urls]
        wait(all_task, return_when=ALL_COMPLETED)
        ColorFormatter('Task Done!').info()

    @staticmethod
    def single_save_picture(target_url, pic_path=PNG_PATH):
        option = webdriver.FirefoxOptions()
        option.add_argument('--headless')
        # 禁用 GPU 硬件加速，防止出现bug
        option.add_argument('--disable-gpu')
        if platform.system() == 'Darwin':
            driver_path = os.path.join(ROOT_PATH, 'geckodriver_mac')
        elif platform.system() == 'Linux':
            driver_path = os.path.join(ROOT_PATH, 'geckodriver_linux')
        else:
            raise "暂时没有 Windows 的"

        driver = webdriver.Firefox(executable_path=driver_path, options=option)

        driver.get(target_url)
        # 最好添加 time.sleep() 避免图片还没下载完, 主程序就退出了
        time.sleep(10)

        # 检查是否有 saved_png 文件夹
        if not os.path.exists(PNG_PATH):
            try:
                os.makedirs(PNG_PATH)
            except:
                pass

        png_name = "{}.{}".format(target_url.split('://')[1], 'png')
        save_png_path = os.path.join(pic_path, png_name)
        result = driver.get_screenshot_as_file(save_png_path)

        if result:
            string = "存活网页的截图保存的位置在: {}, 文件名为: {}".format(
                colored("{}{}".format(pic_path, '/'), 'white'),
                colored(png_name, 'white')
            )

            ColorFormatter(string).success()


class Database(object):
    def __init__(self):
        pass

    @staticmethod
    def init_database():
        # 初始化数据库
        if os.path.exists(DATABASE_FILE):
            try:
                os.makedirs(DATABASE_FILE)
            except:
                pass

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

    def insert_data(self, table_name, data):
        cursor = self.init_database()
        fetch_data_sql = 'SELECT * from {} where url = "{}"'.format(table_name, data)
        select_data = cursor.execute(fetch_data_sql).fetchall()

        if not len(select_data):
            # 如果 select_data 列表为空, 就插入数据
            insert_sql = "INSERT INTO {}(url) VALUES ('{}')".format(table_name, data)
            cursor.execute(insert_sql)

    def show_cached_url(self):
        cursor = self.init_database()
        sql = 'SELECT * FROM cached_online_url ORDER BY url'
        online_urls = cursor.execute(sql).fetchall()
        return online_urls

    def clean_database(self):
        cursor = self.init_database()
        clean_sql = 'DELETE FROM cached_online_url'
        cursor.execute(clean_sql)
        return None


def main():
    section_url = "http://192.168.{}.{}"

    banner()
    opts = CmdLineParser().cmd_parser()

    if not len(sys.argv[1:]):
        ColorFormatter("You failed to provide an option, redirecting to help menu").fatal()
        # 停顿2秒之后再显示 help banner
        time.sleep(2)
        print()
        CmdLineParser().cmd_parser(get_help=True)

    else:
        try:
            # 初始化 database object
            database = Database()
            database.init_database()

            if opts.show_urls:
                cached_urls = database.show_cached_url()

                if cached_urls:
                    ColorFormatter('Show all of the cached urls from database in below').info()

                    print(colored(SPACER, 'white'))
                    for i, url in enumerate(cached_urls):
                        # 计算长度的
                        origin_string = "{}{}{}{}".format(
                            '| ',
                            "#" + str(i) + " ",
                            '| ',
                            url[1]
                        )
                        # 这个是要输出的 字符串
                        string = "{}{}{}{}".format(
                            colored('| ', 'white'),
                            colored("#" + str(i) + " ", 'white'),
                            colored('| ', 'white'),
                            url[1]
                        )

                        space = ' '
                        string += space * (32 - len(origin_string.strip()) - 1) + colored('|', 'white')
                        print(string)

                    print(colored(SPACER, 'white'))
                else:
                    string = 'No cached url from database, please return script and {} {}'.format(
                        colored('type -c INT option', 'white'),
                        colored('to find out HTTP server who used to', 'red')
                    )
                    ColorFormatter(string).fatal()

                sys.exit(0)

            if opts.section:
                # 多线程批量打
                executor = ThreadPoolExecutor(max_workers=opts.thread_number)
                urls = [section_url.format(opts.section, i) for i in range(1, 255)]

                request_obj = Request()
                all_task = [executor.submit(request_obj.send_request, url, opts.verbose, opts.ssl)
                            for url in urls]
                # 等待所有的线程池中的任务完成
                wait(all_task, return_when=ALL_COMPLETED)
                # 下载所有有 web 界面的 banner 截图
                request_obj.save_picture(urls=request_obj.request_result_list, thread_number=opts.thread_number)
                sys.exit(0)

            if opts.target_url:
                # 单个的 url 还是使用多线程, 不使用线程池, 毕竟创建线程池也要耗费资源
                request_obj = Request()
                thread_list = []
                for url in opts.target_url:
                    client_thread = threading.Thread(target=request_obj.send_request,
                                                     args=(url, opts.verbose, opts.ssl,))
                    thread_list.append(client_thread)
                    client_thread.start()
                for _ in thread_list:
                    _.join()

                thread_list = []
                for url in request_obj.request_result_list:
                    client_thread = threading.Thread(target=request_obj.single_save_picture, args=(url,))
                    thread_list.append(client_thread)
                    client_thread.start()
                for _ in thread_list:
                    _.join()

                ColorFormatter('Task Done!').info()
                sys.exit(0)

            if opts.input_file:
                with open(str(opts.input_file), 'rb') as r:
                    url_list = r.readlines()

                # 多线程批量打
                executor = ThreadPoolExecutor(max_workers=opts.thread_number)
                urls = [url.strip().decode('utf8') for url in url_list]

                request_obj = Request()
                all_task = [executor.submit(request_obj.send_request, url, opts.verbose, opts.ssl)
                            for url in urls]
                # 等待所有的线程池中的任务完成
                wait(all_task, return_when=ALL_COMPLETED)

                # 下载所有有 web 界面的 banner 截图
                # 创建以 输入文件名 命名的文件夹
                save_pic_path = os.path.join(PNG_PATH, opts.input_file.split('.')[0])
                if not os.path.exists(save_pic_path):
                    try:
                        os.mkdir(save_pic_path)
                    except:
                        pass

                request_obj.save_picture(urls=request_obj.request_result_list, thread_number=opts.thread_number,
                                      pic_path=save_pic_path)
                sys.exit(0)

            if opts.clean_data:
                if os.path.exists(PNG_PATH):
                    subprocess.Popen("cd {} && {}".format(PNG_PATH, 'rm -rf *'), stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, shell=True)
                if os.path.exists(GECKODRIVER_LOG_FILE):
                    with open(GECKODRIVER_LOG_FILE, 'wb') as w:
                        w.write("")
                # 清除数据库数据
                Database().clean_database()
                ColorFormatter('Clean Done!').fatal()

        except KeyboardInterrupt:
            ColorFormatter("User Abort Scanning").fatal()


class CmdLineParser(ArgumentParser):
    def __init__(self):
        super(CmdLineParser, self).__init__()

    @staticmethod
    def cmd_parser(get_help=False):
        parser = ArgumentParser(prog=sys.argv[0], add_help=False)

        # Helper argument
        helper = parser.add_argument_group('helper arguments')
        helper.add_argument('-h', '--help', help='show this help message and exit', action='help')

        # Mandatory argument
        mandatory = parser.add_argument_group("Mandatory module",
                                              "arguments that have to be passed for the program to run")
        mandatory.add_argument("-c", "--section", type=int, dest="section", metavar="INT",
                               help="type a C section IP address, eg: 2, This is simple option to point ip address "
                                    "section, for example: 192.168.2.0/24. This mean that -c or --section option is 2")
        mandatory.add_argument('-u', '--url', dest='target_url', nargs='+', metavar='TARGET-URL',
                               help='input target url you want to get screenshot, support input multi urls')
        mandatory.add_argument('-i', '--input-file', dest='input_file', metavar='URL-LIST-FILE',
                               help='take the file that contain all of urls you want to scan into here, you can get a '
                                    'list of screenshot with those urls')

        # Options module
        options = parser.add_argument_group("Options module", 'set up parameter to control request')
        options.add_argument('-t', '--thread', dest='thread_number', metavar='INT', default=200,
                               help='set up threads of number, default is 200 count')
        options.add_argument('--ssl', action='store_true', help='toggle ssl for request')

        options.add_argument("-v", "--verbose", action='store_true', dest="verbose", help="toggle verbose mode")

        # Database module
        database = parser.add_argument_group("Database module",
                                             "whether turn on verbose mode to output more details info")
        database.add_argument("-s", "--show-urls", action='store_true', dest="show_urls",
                              help="show all cached urls in database")
        database.add_argument('--clean', action='store_true', dest='clean_data',
                              help='clean the database cache, the Geckodriver redundant log file and saved screenshot files')

        opts = parser.parse_args()

        if get_help:
            return parser.print_help()
        else:
            return opts

if __name__ == '__main__':
    main()

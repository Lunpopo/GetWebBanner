# get_web_banner
This is GetWebBanner script, a very small and simple tool to take screenshot when scanning target network.

This script aim to find out website who using HTTP server and take screenshot to save.

## Feature
1. It can scan an dozen ip address when you specific -s or --section option.

	for example: Typing a C section ip 192.168.2.0/24. This mean that -c or --section option is 2

2. Support thread to scan target network.

## Usage And Argument options
usage: ./get_web_banner.py [-h] [-c INT] [-v]

```
helper arguments:
  -h, --help            show this help message and exit

mandatory arguments:
  arguments that have to be passed for the program to run

  -c INT, --section INT
                        type a C section IP address, eg: 2, This is simple
                        option to point ip address section, for example:
                        192.168.2.0/24. This mean that -c or --section option
                        is 2

verbose arguments:
  whether turn on verbose mode to output more details info

  -v, --verbose         toggle verbose mode
```

## Author
[Lunpopo](https://github.com/Lunpopo/get_web_banner)

You can modify and redistribute this script following GNU License and see alse or more details about GNU License to look through LICENSE file in this repository.

If you have good suggestion or good idea to improve this script, wellcome to contact me in Github, Thanks a lot.

from colorama import init, Fore, Back, Style

init(autoreset=True)


class Color(object):

    #  前景色:红色  背景色:默认
    def red(self, s):
        return Fore.LIGHTRED_EX + s + Fore.RESET

    #  前景色:绿色  背景色:默认
    def green(self, s):
        return Fore.LIGHTGREEN_EX + s + Fore.RESET

    #  前景色:黄色  背景色:默认
    def yellow(self, s):
        return Fore.LIGHTYELLOW_EX + s + Fore.RESET

    #  前景色:蓝色  背景色:默认
    def blue(self, s):
        return Fore.LIGHTBLUE_EX + s + Fore.RESET

    #  前景色:洋红色  背景色:默认
    def magenta(self, s):
        return Fore.LIGHTMAGENTA_EX + s + Fore.RESET

    #  前景色:青色  背景色:默认
    def cyan(self, s):
        return Fore.LIGHTCYAN_EX + s + Fore.RESET

    #  前景色:白色  背景色:默认
    def white(self, s):
        return Fore.LIGHTWHITE_EX + s + Fore.RESET

    #  前景色:黑色  背景色:默认
    def black(self, s):
        return Fore.LIGHTBLACK_EX + s + Fore.RESET

    #  前景色:白色  背景色:绿色
    def white_green(self, s):
        return Fore.LIGHTWHITE_EX + Back.LIGHTGREEN_EX + s + Fore.RESET + Back.RESET

color = Color()

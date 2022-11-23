"Various utilities for pi_framework"

import colorama

colorama.init()
class PrintColor:
    r = colorama.Fore.RED
    g = colorama.Fore.GREEN
    y = colorama.Fore.YELLOW
    b = colorama.Fore.CYAN

    e = colorama.Fore.RESET


__all__ = ['PrintColor']
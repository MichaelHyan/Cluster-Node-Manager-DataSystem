from colorama import init, Fore, Back, Style
init()
class Color:
    BLACK = Fore.BLACK
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    RESET = Fore.RESET

    BG_BLACK = Back.BLACK
    BG_RED = Back.RED
    BG_GREEN = Back.GREEN
    BG_YELLOW = Back.YELLOW
    BG_BLUE = Back.BLUE
    BG_MAGENTA = Back.MAGENTA
    BG_CYAN = Back.CYAN
    BG_WHITE = Back.WHITE
    BG_RESET = Back.RESET

    BRIGHT = Style.BRIGHT
    DIM = Style.DIM
    NORMAL = Style.NORMAL
    RESET_ALL = Style.RESET_ALL


def print_color(text: str, color: str = Color.RED, bg: str = None) -> None:
    prefix = color
    if bg:
        prefix += bg
    print(f"{prefix}{text}{Color.RESET}")


def print_success(text: str) -> None:
    print_color(text, Color.GREEN)


def print_warning(text: str) -> None:
    print_color(text, Color.YELLOW)


def print_error(text: str) -> None:
    print_color(text, Color.RED)


def print_info(text: str) -> None:
    print_color(text, Color.CYAN)


def print_debug(text: str) -> None:
    print_color(text, Color.WHITE)


def color_text(text: str, color: str = Color.RED) -> str:
    return f"{color}{text}{Color.RESET}"
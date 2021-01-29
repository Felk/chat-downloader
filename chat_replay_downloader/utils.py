import threading
import colorlog
import datetime
import re
import sys
import os
import locale
import collections.abc
import io


def timestamp_to_microseconds(timestamp):
    """
    Convert RFC3339 timestamp to microseconds.
    This is needed as datetime.datetime.strptime() does not support nanosecond precision.
    """
    info = list(filter(None, re.split('[\.|Z]{1}', timestamp))) + [0]
    return round((datetime.datetime.strptime('{}Z'.format(info[0]), '%Y-%m-%dT%H:%M:%SZ').timestamp() + float('0.{}'.format(info[1])))*1e6)


def time_to_seconds(time):
    """Convert timestamp string of the form 'hh:mm:ss' to seconds."""
    return int(sum(abs(int(x)) * 60 ** i for i, x in enumerate(reversed(time.replace(',', '').split(':')))) * (-1 if time[0] == '-' else 1))


# def seconds_to_time(seconds):
#     """Convert seconds to timestamp."""
#     t = datetime.timedelta(0, abs(seconds))
#     # time_string = t.days()
#     return ('-' if seconds < 0 else '') + re.sub(r'^0:0?', '', str(t))

def seconds_to_time(seconds):
    """Convert seconds to timestamp."""
    h, remainder = divmod(abs(seconds), 3600)
    m, s = divmod(remainder, 60)
    time_string = '{}:{:02}:{:02}'.format(int(h), int(m), int(s))
    return ('-' if s < 0 else '') + re.sub(r'^0:0?', '', str(time_string))


def microseconds_to_timestamp(microseconds, format='%Y-%m-%d %H:%M:%S'):
    """Convert unix time to human-readable timestamp."""
    return datetime.datetime.fromtimestamp(microseconds//1000000).strftime(format)


def ensure_seconds(time, default=None):
    """Ensure time is returned in seconds."""
    if time is None:  # if time is none, return default
        return default

    try:
        return int(time)
    except ValueError:
        return time_to_seconds(time)
    except:
        return default


def arbg_int_to_rgba(argb_int):
    """Convert ARGB integer to RGBA array."""
    red = (argb_int >> 16) & 255
    green = (argb_int >> 8) & 255
    blue = argb_int & 255
    alpha = (argb_int >> 24) & 255
    return [red, green, blue, alpha]


def rgba_to_hex(colours):
    """Convert RGBA array to hex colour."""
    return '#{:02x}{:02x}{:02x}{:02x}'.format(*colours)


def get_colours(argb_int):
    """Given an ARGB integer, return both RGBA and hex values."""
    rgba_colour = arbg_int_to_rgba(argb_int)
    hex_colour = rgba_to_hex(rgba_colour)
    return {
        'argb_int': argb_int,
        'rgba': rgba_colour,
        'hex': hex_colour
    }

# from youtube-dl


def try_get(src, getter, expected_type=None):
    # used when a method is needed
    # or list/number index retrieval
    if not isinstance(getter, (list, tuple)):
        getter = [getter]
    for get in getter:
        try:
            v = get(src)
        except (AttributeError, KeyError, TypeError, IndexError):
            pass
        else:
            if expected_type is None or isinstance(v, expected_type):
                return v


def get_title_of_webpage(html):
    match = re.search('<title(?:[^>]*)>(.*?)</title>', html)
    return match.group(1) if match else None


def int_or_none(v, default=None):
    try:
        return int(v)
    except (ValueError, TypeError):
        return default


def try_get_first_key(dictionary, default=None):
    try:
        return next(iter(dictionary))
    except:
        return default


def try_get_first_value(dictionary, default=None):
    try:
        return next(iter(dictionary.values()))
    except:
        return default


def remove_prefixes(text, prefixes):
    if not isinstance(prefixes, (list, tuple)):
        prefixes = [prefixes]

    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):]

    return text


def remove_suffixes(text, suffixes):
    if not isinstance(suffixes, (list, tuple)):
        suffixes = [suffixes]

    for suffix in suffixes:
        if text.endswith(suffix):
            text = text[0:-len(suffix):]

    return text


def update_dict_without_overwrite(original, new):
    original.update({key: new[key] for key in new if key not in original})


def camel_case_split(word):
    return '_'.join(re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', word)).lower()


def supports_colour():
    """
    Return True if the running system's terminal supports colour,
    and False otherwise.
    """
    def vt_codes_enabled_in_windows_registry():
        """
        Check the Windows Registry to see if VT code handling has been enabled
        by default, see https://superuser.com/a/1300251/447564.
        """
        try:
            # winreg is only available on Windows.
            import winreg
        except ImportError:
            return False
        else:
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Console')
            try:
                reg_key_value, _ = winreg.QueryValueEx(
                    reg_key, 'VirtualTerminalLevel')
            except FileNotFoundError:
                return False
            else:
                return reg_key_value == 1

    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

    return is_a_tty and (
        sys.platform != 'win32' or
        'ANSICON' in os.environ or
        # Windows Terminal supports VT codes.
        'WT_SESSION' in os.environ or
        # Microsoft Visual Studio Code's built-in terminal supports colours.
        os.environ.get('TERM_PROGRAM') == 'vscode' or
        vt_codes_enabled_in_windows_registry()
    )


if supports_colour():
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '[%(log_color)s%(levelname)s%(reset)s] %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        })
    )
    logger = colorlog.getLogger()  # 'root'
else:  # fallback support
    import logging
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger = logging.getLogger()


logger.addHandler(handler)


def pause(text='Press Enter to continue...'):
    input(text)


def set_log_level(level):
    logger.setLevel(level.upper())

def get_logger():
    return logger

def log(level, items, to_pause=False):
    l = getattr(logger, level, None)
    if l:
        if not isinstance(items, (tuple, list)):
            items = [items]
        for item in items:
            l(item)

        if to_pause:
            pause()


def replace_with_underscores(text, sep='-'):
    return text.replace(sep, '_')


def multi_get(dictionary, *keys, default=None):
    current = dictionary
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        elif isinstance(current, (list, tuple)) and isinstance(key, int) and key < len(current):
            current = current[key]
        else:
            return default
    return current


def flatten_json(original_json):
    final = {}

    def flatten(item, prefix=''):
        if isinstance(item, dict):
            for key in item:
                flatten(item[key], '{}{}.'.format(prefix, key))
        elif isinstance(item, list):
            for index in range(len(item)):
                flatten(item[index], '{}{}.'.format(prefix, index))
        else:
            final[prefix[:-1]] = item
    flatten(original_json)

    return final


def attempts(max_attempts):
    return range(1, max_attempts+1)


def preferredencoding():
    """Get preferred encoding.
    Returns the best encoding scheme for the system, based on
    locale.getpreferredencoding() and some further tweaks.
    """
    try:
        pref = locale.getpreferredencoding()
        'TEST'.encode(pref)
    except Exception:
        pref = 'utf-8'

    return pref


def _windows_write_string(s, out, skip_errors=True):
    """ Returns True if the string was written using special methods,
    False if it has yet to be written out."""
    # Adapted from http://stackoverflow.com/a/3259271/35070

    import ctypes
    import ctypes.wintypes

    WIN_OUTPUT_IDS = {
        1: -11,
        2: -12,
    }

    try:
        fileno = out.fileno()
    except AttributeError:
        # If the output stream doesn't have a fileno, it's virtual
        return False
    except io.UnsupportedOperation:
        # Some strange Windows pseudo files?
        return False
    if fileno not in WIN_OUTPUT_IDS:
        return False

    GetStdHandle = ctypes.WINFUNCTYPE(
        ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD)(
        ('GetStdHandle', ctypes.windll.kernel32))
    h = GetStdHandle(WIN_OUTPUT_IDS[fileno])

    WriteConsoleW = ctypes.WINFUNCTYPE(
        ctypes.wintypes.BOOL, ctypes.wintypes.HANDLE, ctypes.wintypes.LPWSTR,
        ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD),
        ctypes.wintypes.LPVOID)(('WriteConsoleW', ctypes.windll.kernel32))
    written = ctypes.wintypes.DWORD(0)

    GetFileType = ctypes.WINFUNCTYPE(ctypes.wintypes.DWORD, ctypes.wintypes.DWORD)(
        ('GetFileType', ctypes.windll.kernel32))
    FILE_TYPE_CHAR = 0x0002
    FILE_TYPE_REMOTE = 0x8000
    GetConsoleMode = ctypes.WINFUNCTYPE(
        ctypes.wintypes.BOOL, ctypes.wintypes.HANDLE,
        ctypes.POINTER(ctypes.wintypes.DWORD))(
        ('GetConsoleMode', ctypes.windll.kernel32))
    INVALID_HANDLE_VALUE = ctypes.wintypes.DWORD(-1).value

    def not_a_console(handle):
        if handle == INVALID_HANDLE_VALUE or handle is None:
            return True
        return ((GetFileType(handle) & ~FILE_TYPE_REMOTE) != FILE_TYPE_CHAR
                or GetConsoleMode(handle, ctypes.byref(ctypes.wintypes.DWORD())) == 0)

    if not_a_console(h):
        return False

    def next_nonbmp_pos(s):
        try:
            return next(i for i, c in enumerate(s) if ord(c) > 0xffff)
        except StopIteration:
            return len(s)

    while s:
        count = min(next_nonbmp_pos(s), 1024)

        ret = WriteConsoleW(
            h, s, count if count else 2, ctypes.byref(written), None)
        if ret == 0:
            if skip_errors:
                continue
            else:
                raise OSError('Failed to write string')
        if not count:  # We just wrote a non-BMP character
            assert written.value == 2
            s = s[1:]
        else:
            assert written.value > 0
            s = s[written.value:]
    return True


def safe_print(*objects, sep=' ', end='\n', out=None, encoding=None, flush=False):
    """
    Ensure printing to standard output can be done safely (especially on Windows).
    There are usually issues with printing emojis and non utf-8 characters.

    """
    output_string = sep.join(map(lambda x: str(x), objects)) + end

    if out is None:
        out = sys.stdout

    if sys.platform == 'win32' and encoding is None and hasattr(out, 'fileno'):
        if _windows_write_string(output_string, out):
            return

    if 'b' in getattr(out, 'mode', '') or not hasattr(out, 'buffer'):
        out.write(output_string)
    else:
        enc = encoding or getattr(out, 'encoding', None) or preferredencoding()
        byt = output_string.encode(enc, 'ignore')
        out.buffer.write(byt)

    if flush and hasattr(out, 'flush'):
        out.flush()


def nested_update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = nested_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


# Inspired by https://github.com/hero24/TimedInput/
from threading import Thread


class TimedInput(Thread):
    """ Timed input reader """

    def get_input(self):
        """ Actual function for reading the input """
        try:
            print(self.prompt, end='', flush=True)
            self.input = input()
        except EOFError:
            pass

    def __init__(self, timeout, prompt='', default=None, *args, **kwargs):
        """
        TimedInput(
            timeout -> amount of seconds to wait for the input,
            prompt -> optionl prompt to display while asking for input,
            default -> string to return in case of timeout,
            *args/**kwargs -> any additional arguments are passed down to Thread
                            constructor
        )
        Creates an object for reading input, that times out after `timeout` amount
                of seconds.
        """
        self.timeout = timeout
        self.prompt = prompt
        self.input = default
        super().__init__(target=self.get_input, *args, **kwargs)
        self.daemon = True

    def join(self):
        """ The actual timeout happens here """
        super().join(self.timeout)
        return self.input

    def read(self):
        """ Reads the input from the reader """
        self.start()
        return self.join()


def timed_input(timeout=None, prompt='', default=None, *args, **kwargs):
    if timeout is None:
        return input(prompt)
    else:
        return TimedInput(timeout, prompt, default, *args, **kwargs).read()


import inspect
def get_default_args(func):
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        # if k != 'self'
        if v.default is not inspect.Parameter.empty
    }
    # TODO get required args

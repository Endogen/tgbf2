def is_numeric(string) -> bool:
    """ Also accepts '.' in the string. Function 'isnumeric()' doesn't """
    try:
        float(string)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(string)
        return True
    except (TypeError, ValueError):
        pass

    return False


def format(value,
           decimals=None,
           force_length=False,
           template=None,
           on_zero=0,
           on_none=None,
           symbol=None):
    """ Format a crypto coin value so that it isn't unnecessarily long """

    fiat = False

    if symbol and isinstance(symbol, str):
        pass
    if value is None:
        return on_none
    try:
        if isinstance(value, str):
            value = value.replace(",", "")
        v = float(value)
    except:
        return str(value)
    try:
        if isinstance(template, str):
            template = template.replace(",", "")
        t = float(template)
    except:
        t = v
    try:
        decimals = int(decimals)
    except:
        decimals = None
    try:
        if float(value) == 0:
            return on_zero
    except:
        return str(value)

    if t < 1:
        if decimals:
            v = "{1:.{0}f}".format(decimals, v)
        else:
            v = "{0:.8f}".format(v)
    elif t < 100:
        if decimals:
            v = "{1:.{0}f}".format(decimals, v)
        else:
            v = "{0:.4f}".format(v)
    elif t < 10000:
        if decimals:
            v = "{1:,.{0}f}".format(decimals, v)
        else:
            v = "{0:,.2f}".format(v)
    else:
        v = "{0:,.0f}".format(v)

    if not force_length:
        cut_zeros = False

        if t >= 1:
            cut_zeros = True
        else:
            if fiat:
                cut_zeros = True

        if cut_zeros:
            while "." in v and v.endswith(("0", ".")):
                v = v[:-1]
    return v


def build_menu(buttons, n_cols=1, header_buttons=None, footer_buttons=None):
    """ Build button-menu for Telegram """
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]

    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)

    return menu


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


def split_msg(msg, max_len=None, split_char="\n", only_one=False):
    """ Restrict message length to max characters as defined by Telegram """
    if not max_len:
        import constants as con
        max_len = con.MAX_TG_MSG_LEN

    if only_one:
        return [msg[:max_len][:msg[:max_len].rfind(split_char)]]

    remaining = msg
    messages = list()

    while len(remaining) > max_len:
        split_at = remaining[:max_len].rfind(split_char)
        message = remaining[:max_len][:split_at]
        messages.append(message)
        remaining = remaining[len(message):]
    else:
        messages.append(remaining)

    return messages


def encode_url(trxid):
    import urllib.parse as ul
    return ul.quote_plus(trxid)


def random_id(length=8):
    import string, random
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(random.choices(alphabet, k=length))


def md5(input_str: str, to_int=False):
    import hashlib
    md5_hash = hashlib.md5(input_str.encode("utf-8")).hexdigest()
    return int(md5_hash, 16) if to_int else md5_hash


def to_unix_time(date_time, millis=False):
    from datetime import datetime
    seconds = (date_time - datetime(1970, 1, 1)).total_seconds()
    return int(seconds * 1000 if millis else seconds)


def from_unix_time(seconds, millis=False):
    from datetime import datetime
    return datetime.utcfromtimestamp(seconds / 1000 if millis else seconds)


def get_ip():
    import socket
    return socket.gethostbyname(socket.gethostname())


def get_external_ip():
    import urllib.request
    return urllib.request.urlopen('https://api.ipify.org/').read().decode("utf-8")

#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Gabel, the static site generator for gabl.ink."""

import json
import re
import sys
import time
from datetime import date
from pathlib import Path

__author__ = "gabl.ink"
__version__ = "0"


class L:
    """Simpler replacement for the ``Language`` class from
    ``langcodes``.

    Supports all subtags except for extensions (``t`` and ``u``).

    Works perfectly! If the tag is already well‐formed.
    """
    def __init__(self, l: str, s: str | None = None, t: str | None = None,
                 v: list[str] | None = None, x: str | None = None):
        self.l: str = l
        self.s: str | None = s
        self.t: str | None = t
        self.v: list[str] | None = v
        self.x: str | None = x

    @classmethod
    def make(cls, l: str, s: str | None = None, t: str | None = None,
             v: list[str] | None = None, x: str | None = None) -> "L":
        return cls(l, s, t, v, x)

    @staticmethod
    def get(tag: "str|L") -> "L":
        if isinstance(tag, L):
            return tag

        if not isinstance(tag, str) or not tag:
            raise ValueError("Invalid language code")

        langdata: dict = {}
        subtags: list[str] = tag.split("-")
        it: int = 0

        for subtag in subtags:
            if it == 0:
                if re.fullmatch(r"^[A-Za-z]{2,3}$", subtag):
                    langdata["l"] = subtag.lower()
                    it += 1
                else:
                    raise ValueError("Invalid language code")
            # TODO: do this kind of normalization everywhere
            else:
                if re.fullmatch(r"^[A-Za-z]{4}$", subtag):
                    if not langdata.get("t"):
                        langdata["s"] = subtag.capitalize()
                    else:
                        raise ValueError("Invalid language code")
                elif re.fullmatch(r"^[A-Za-z]{2}$|^[0-9]{3}$", subtag):
                    langdata["t"] = subtag.upper()
                elif re.fullmatch(r"^[A-Za-z]{5,8}$|^[0-9][A-Za-z0-9]{3}$", subtag):
                    if not langdata.get("v"):
                        langdata["v"] = [subtag.lower()]
                    else:
                        langdata["v"].append(subtag.lower())
                elif subtag == "x":
                    langdata["x"] = "-".join(subtags[it+1:].lower())
                    break
                else:
                    raise ValueError("Invalid or unsupported language code")

        return L.make(**langdata)

    def __str__(self) -> str:
        if not isinstance(self.l, str) or not self.l:
            raise ValueError("Invalid language code")

        r: list[str] = [self.l]

        if self.s:
            r.append(f"-{self.s}")

        if self.t:
            r.append(f"-{self.t}")

        if self.v:
            for v in self.v:
                r.append(f"-{v}")

        if self.x:
            r.append(f"-x-{self.x}")

        return "".join(r)


def attr(string: str, fformat: str | None = None) -> str:
    """Takes a plain text string as input and returns the HTML
    component that comes right after the attribute name. Returns an
    empty string if the input is empty. Returns the equals sign,
    quotation marks as appropriate, and the string with characters
    escapes as necessary if the input is not empty.

    >>> attr("")
    ''
    >>> attr("hello, world")
    '="hello, world"'
    >>> attr("&")
    '=&'
    >>> attr("&amp;")
    '=&amp;amp;'
    >>> attr("'")
    '="\\'"'
    >>> attr('"')
    '=\\'"\\''
    """
    if not isinstance(string, str):
        raise TypeError("Not a string")
    if fformat is None:
        fformat = format

    if not string:
        if fformat == "X":
            return '=""'
        else:
            # In HTML5, `attribute` is equivalent to `attribute=""`
            return ""

    quoted: bool

    if fformat == "X":
        quoted = True
    elif any(c in string for c in " \"'=<>`\n\r\t\v\f"):
        quoted = True
    else:
        quoted = False

    quote_char: str

    if quoted:
        if '"' in string and "'" not in string:
            quote_char = "'"
        elif "'" in string and '"' not in string:
            quote_char = '"'
        elif '"' in string and "'" in string:
            if string.count('"') > string.count("'"):
                quote_char = "'"
            else:
                quote_char = '"'
        else:
            quote_char = '"'

    string = re.sub(r"&(?=[#A-Za-z])", "&amp;", string)  # &#38;

    if quoted:
        if quote_char == '"':
            string = string.replace('"', "&#34;")  # &quot;
        elif quote_char == "'":
            string = string.replace("'", "&#39;")  # &apos;
        return f"={quote_char}{string}{quote_char}"
    else:
        return f"={string}"


def close_tag(tag: str, fformat: str | None = None):
    if fformat is None:
        fformat = format
    if fformat == "X":
        return f"</{tag}>"
    else:
        return ""


def expand_parts(parts: list[str | int]) -> list[int]:
    """Returns a list of integers from a ``parts`` list.

    >>> expand_parts([1, 2, 3])
    [1, 2, 3]
    >>> expand_parts(["1-3"])
    [1, 2, 3]
    >>> expand_parts([4, 7, "1-5"])
    [1, 2, 3, 4, 5, 7]
    """
    result: set[int] = set()

    for part in parts:
        if isinstance(part, int):
            result.add(part)
        else:
            start, end = map(int, part.split("-"))
            result.update(range(start, end + 1))

    return sorted(result)


def get_i(i_item_file: Path) -> str:
    with open(i_item_file, "r", encoding="utf-8") as f:
        item_obj = json.load(f)
        return item_obj["id"]


def get_var_l10n(index, key: str, fformat: str | None = None, flang: L | None = None) -> str:
    if flang is None:
        flang = lang
    if fformat is None:
        fformat = format

    formats: str = "AHiLpTtX"
    real_formats: str = "HiLptX"
    options: list[str] = [f"{flang}", flang.l, "mul", "zxx", "z"]

    if fformat not in real_formats:
        raise ValueError("Invalid real format given")

    def find_equals(pointer: str) -> str:
        to_find: tuple = index[key][o][f"{pointer}e"].rpartition("_")

        # TODO: catch invalid equals
        if to_find[2] and to_find[2] not in formats:
            raise ValueError("Equals does not contain a valid format")
        elif to_find[2] and not to_find[1]:
            return get_var_l10n(index, key, to_find[2], flang)
        elif to_find[0] and not to_find[1]:
            return get_var_l10n(index, key, fformat, to_find[0])
        else:
            return get_var_l10n(index, key, to_find[2], to_find[0])

    # ASCII

    # HTML5
    if fformat == "H":
        for o in options:
            if o == "z":
                return ""

            to_check: dict = index.get(key, {}).get(o, {})

            if "H" in to_check:
                return to_check["H"]
            elif "Hf" in to_check:
                return eval(f'f"{to_check["Hf"]}"')
            elif "He" in to_check:
                return find_equals("H")
            elif "t" in to_check:
                return text_to_html(to_check["t"])
            elif "tf" in to_check:
                # TODO: Not tested and maybe wrong
                return eval(f'{text_to_html(f"{to_check["tf"]}")}')
            elif "te" in to_check:
                return text_to_html(find_equals("t"))
            elif "A" in to_check:
                return text_to_html(to_check["A"])
            elif "Af" in to_check:
                return eval(f'f"{to_check["Af"]}"')
            elif "Ae" in to_check:
                return text_to_html(find_equals("A"))
            elif "e" in to_check:
                return get_var_l10n(index, key, fformat,
                                    L.get(to_check["e"]))
    # identifier
    elif fformat == "i":
        for o in options:
            if o == "z":
                return ""

            to_check: dict = index.get(key, {}).get(o, {})
            
            if "i" in to_check:
                return to_check["i"]
            elif "if" in to_check:
                return eval(f'f"{to_check["if"]}"')
            elif "ie" in to_check:
                return find_equals("i")
            elif "e" in to_check:
                return get_var_l10n(index, key, fformat,
                                    L.get(to_check["e"]))
    # LaTeX
    elif fformat == "L":
        for o in options:
            if o == "z":
                return ""
                    
            to_check: dict = index.get(key, {}).get(o, {})

            if "L" in to_check:
                return to_check["L"]
            elif "Lf" in to_check:
                return eval(f'f"{to_check["Lf"]}"')
            elif "Le" in to_check:
                return find_equals("L")
            elif "T" in to_check:
                return to_check["T"]
            elif "Tf" in to_check:
                return eval(f'f"{to_check["Tf"]}"')
            elif "Te" in to_check:
                return find_equals("T")
            elif "t" in to_check:
                return text_to_latex(to_check["t"])
            elif "tf" in to_check:
                return eval(f'{text_to_latex(f"{to_check["tf"]}")}')
            elif "te" in to_check:
                return text_to_latex(find_equals("t"))
            elif "A" in to_check:
                return text_to_latex(to_check["A"])
            elif "Af" in to_check:
                return eval(f'{text_to_latex(f"{to_check["Af"]}")}')
            elif "Ae" in to_check:
                return text_to_latex(find_equals("A"))
            elif "e" in to_check:
                return get_var_l10n(index, key, fformat,
                                    L.get(to_check["e"]))
    # print
    elif fformat == "p":
        for o in options:
            if o == "z":
                return ""
            
            to_check: dict = index.get(key, {}).get(o, {})

            if "p" in to_check:
                return to_check["p"]
            elif "pf" in to_check:
                return eval(f'f"{to_check["pf"]}"')
            elif "pe" in to_check:
                return find_equals("p")
            elif "t" in to_check:
                return to_check["t"]
            elif "tf" in to_check:
                return eval(f'f"{to_check["tf"]}"')
            elif "te" in to_check:
                find_equals("t")
            elif "A" in to_check:
                return to_check["A"]
            elif "Ae" in to_check:
                return find_equals("A")
            elif "e" in to_check:
                return get_var_l10n(index, key, fformat,
                                    L.get(to_check["e"]))
    # TeX

    # text
    elif fformat == "t":
        for o in options:
            if o == "z":
                return ""

            to_check: dict = index.get(key, {}).get(o, {})

            if "t" in to_check:
                return to_check["t"]
            elif "tf" in to_check:
                return eval(f'f"{to_check["tf"]}"')
            elif "te" in to_check:
                return find_equals("t")
            elif "A" in to_check:
                return to_check["A"]
            elif "Af" in to_check:
                return eval(f'f"{to_check["Af"]}"')
            elif "Ae" in to_check:
                return find_equals("A")
            elif "e" in to_check:
                return get_var_l10n(index, key, fformat,
                                    L.get(to_check["e"]))
    # XHTML5 (polyglot)
    elif fformat == "X":
        for o in options:
            if o == "z":
                return ""

            to_check: dict = index.get(key, {}).get(o, {})

            if "X" in to_check:
                return to_check["X"]
            elif "Xf" in to_check:
                return eval(f'f"{to_check["Xf"]}"')
            elif "Xe" in to_check:
                return find_equals("X")
            elif "H" in to_check:
                return to_check["H"]
            elif "Hf" in to_check:
                return eval(f'f"{to_check["Hf"]}"')
            elif "He" in to_check:
                return find_equals("H")
            elif "t" in to_check:
                return text_to_html(to_check["t"])
            elif "tf" in to_check:
                return eval(f'f"{to_check["tf"]}"')
            elif "te" in to_check:
                return text_to_html(find_equals("t"))
            elif "A" in to_check:
                return text_to_html(to_check["A"])
            elif "Af" in to_check:
                return eval(f'f"{to_check["Af"]}"')
            elif "Ae" in to_check:
                return text_to_html(find_equals("A"))
            elif "e" in to_check:
                return get_var_l10n(index, key, fformat,
                                    L.get(to_check["e"]))


def id_base(id_i: str) -> str:
    """Returns the base part of an ID.

    >>> id_base("foo")
    'foo'
    >>> id_base("foo/bar")
    'bar'
    >>> id_base("foo/bar/baz")
    'baz'
    """
    if "/" in id_i:
        return id_i.rpartition("/")[2]
    else:
        return id_i


def id_parent(id_i: str) -> str | None:
    """Returns the non‐base part of an ID.

    >>> id_parent("foo")

    >>> id_parent("foo/bar")
    'foo'
    >>> id_parent("foo/bar/baz")
    'foo/bar'
    """
    if "/" in id_i:
        return id_i.rpartition("/")[0]
    else:
        return None


def language_list_entry(l: L) -> str:
    r: list[str] = ["<li"]

    if l.t is not None:
        r.append(
            f''' style="list-style-type:'{to_regional_indicators(l.t)} '">'''
        )

    if f"{l}" == f"{lang}":
        r.append("<b>")
    else:
        r.append(f"<a lang={l} href=../{f"{l}".lower()}/ hreflang={l}>")

    r.append(say_lang(l, None, l))

    if f"{l}" == f"{lang}":
        r.append("</b>")
    else:
        r.append("</a>")

    return "".join(r)


def make_nav_button(button: str, flang: None | L = None) -> str:
    if flang is None:
        flang = lang

    button_arrow, button_id, button_fl = {
        "f": ("⇦", "first", "first"),
        "p": ("←", "prev", "first"),
        "n": ("→", "next", "last"),
        "l": ("⇨", "last", "last"),
    }[button]

    r: list[str] = ["<div class=B title"]

    if (
        data[i]["location"]["page"]
        == data[data[i]["location"]["series"]].get(button_fl)
    ):
        r.append(
            f"{attr(msg_l10n(msg_l10n(flang=flang, string=f"nav_button_{button_id}_inline"), flang=flang, string="this_is_x_page"))}"
            ">"
        )
    else:
        if button in ("f", "l"):
            r.append(attr(msg_l10n(get_var_l10n(data[f"{data[i]["location"]["series"]}/{data[data[i]["location"]["series"]][button_id]}"], "title", "t"), flang=flang, string="nav_button_page_title")))
        elif button in ("p", "n"):
            r.append(attr(msg_l10n(get_var_l10n(data[f"{data[i]["location"]["series"]}/{data[i]["location"][button_id]}"], "title", "t"), string="nav_button_page_title")))
        r.append("><a href=../../")
        if button in ("f", "l"):
            r.append(f"{data[data[i]["location"]["series"]][button_id]}")
        elif button in ("p", "n"):
            r.append(f"{data[i]["location"][button_id]}")
        r.append(f"/{f"{flang}".lower()}/ hreflang={flang}>")

    r.append(f"<span class=A aria-hidden=true>{button_arrow}</span><br>{msg_l10n(flang=flang, string=f"nav_button_{button_id}")}")

    if (
        data[i]["location"]["page"]
        != data[data[i]["location"]["series"]].get(button_fl, {})
    ):
        r.append("</a>")

    r.append("</div>")

    return "".join(r)


#def make_share_link(name: str) -> str:
#    r: list[str] = [f"<li id=share_link_{name}>"]
#    r.append("<a href")
#
#    query: dict = {}
#    for key in "title", "url", "text", "hashtag":
#        if ddict["share"][name].get(key, {}).get("key"):
#            pass
#
#    r.append(ddict["share"][name]["base"])


def msg_l10n(*args, string: str, flang: L | None = None) -> str:
    if flang is None:
        flang = lang
    return get_var_l10n(ddict["string"], string, "p", flang).format(*args)


def print_date(d: date) -> str:
    """Returns a date string suitable for an HTML ``datetime``
    attribute.

    >>> print_date(date.fromisoformat("20260407"))
    '2026-04-07'
    """
    return f"{d.year:04}-{d.month:02}-{d.day:02}"


def text_to_html(string: str) -> str:
    string = re.sub(r"&(?=[#A-Za-z])", "&amp;", string)  # &#38;
    string = string.replace("<", "&lt;")  # &#60;
    string = string.replace("\u200b", "<wbr>")
    string = string.replace("\n", "<br>")
    return string


def text_to_latex(string: str) -> str:
    for C, R in [("\\", "textbackslash"), ('"', "textquotedbl"),
                 ("'", "textquotesingle"), ("^", "textasciicircum"),
                 ("~", "textasciitilde")]:
        C = re.escape(C)
        string = re.sub(fr"{C}(?=[A-Za-z])", lambda _: f"\\{R} ", string)
        string = re.sub(fr"{C}(?![A-Za-z])(?! )", lambda _: f"\\{R}", string)
        string = re.sub(fr"{C}(?= )", lambda _: f"\\{R}\\", string)
    for c in "#$%&_{}":
        string = string.replace(c, f"\\{c}")
    for q, w in [("\xa0", "~"), ("‐", "-"), ("–", "--"), ("—", "---"),
                 ("‘", "`"), ("’", "'"), ("``", "“"), ("''", "”"),
                 ("\u202f", "\\,"), ("−", "\\(-\\)")]:
        string = string.replace(q, w)
    return string


def to_regional_indicators(string: str) -> str:
    """Returns a set of regional indicators from an uppercase string.

    >>> to_regional_indicators("HELLOWORLDS")
    '🇭🇪🇱🇱🇴🇼🇴🇷🇱🇩🇸'
    >>> to_regional_indicators("US")
    '🇺🇸'
    """
    out_chars: list[str] = []
    for ch in string:
        out_chars.append(chr(0x1f1e6+(ord(ch)-65)))
    return "".join(out_chars)


def to_sentence_case(string: str, flang: L | None = None) -> str:
    """Capitalizes the first character of a string as appropriate for
    the language.

    >>> to_sentence_case("toki pona", L.get("tok"))
    'toki pona'
    >>> to_sentence_case("français", L.get("fr"))
    'Français'
    """
    if flang is None:
        flang = lang

    if flang.l == "tok":
        return string
    else:
        return f"{string[:1].upper()}{string[1:]}"


# The shell script supports negative years, but `datetime` does not.
def say_date(d: date, flang: L | None = None) -> str:
    """Returns word form of date in HTML format.

    >>> say_date(date.fromisoformat("19971225"), L.get("en-US"))
    '<time datetime=1997-12-25>December\xa025, 1997</time>'
    >>> say_date(date.fromisoformat("19971225"), L.get("en-GB"))
    '<time datetime=1997-12-25>25\xa0December 1997</time>'
    >>> say_date(date.fromisoformat("20220401"), L.get("fr"))
    '<time datetime=2022-04-01>1er\xa0avril 2022</time>'
    """
    if flang is None:
        flang = lang

    r: list[str] = [f"<time datetime={print_date(d)}>"]

    ad: bool

    if d.year > 0 and d.year < 1000:
        ad = True
    else:
        ad = False

    if flang.l == "en":
        if flang.t == "US":
            r.append(
                f"{get_var_l10n(ddict["month"]["months"][d.month-1], "name")}"
                f"\xa0{d.day}, "
            )
        elif flang.t == "GB":
            r.append(
                f"{d.day}\xa0"
                f"{get_var_l10n(ddict["month"]["months"][d.month-1], "name")}"
                " "
            )
        if ad:
            r.append("AD\xa0")
        r.append(f"{d.year}")
    elif flang.l == "fr":
        if d.day == 1:
            r.append("1er")
        else:
            r.append(f"{d.day}")
        r.append(
            "\xa0"
            f"{get_var_l10n(ddict["month"]["months"][d.month-1], "name")}"
        )
        if ad:
            r.append(f"{d.year}\xa0ap.\xa0J.‑C.")
        r.append(f" {d.year}")
    elif flang.l == "es":
        r.append(
            f"{d.day}\xa0de\xa0"
            f"{get_var_l10n(ddict["month"]["months"][d.month-1], "name")}"
            " de "
        )
        if ad:
            r.append(f"{d.year}\xa0d.\xa0C.")
        r.append(f"{d.year}")
    elif flang.l in ("ja", "ko", "zh"):
        r.append(
            f"{d.year}{msg_l10n(flang=flang, string="say_date_cjk_year")}"
            f"{d.month}{msg_l10n(flang=flang, string="say_date_cjk_month")}"
            f"{d.day}{msg_l10n(flang=flang, string="say_date_cjk_day")}"
        )

    r.append("</time>")

    return "".join(r)


def say_lang(to_say: L, fformat: str | None = None, flang: L | None = None) -> str:
    """Returns a formatted language name and region.

    >>> say_lang(L.get("en-US"), "t", L.get("en"))
    'English (United States)'
    >>> say_lang(L.get("fr-FR"), "t", L.get("fr"))
    'Français (France)'
    >>> say_lang(L.get("ru-RU"), "t", L.get("en"))
    'Russian (Russia)'
    """
    if flang is None:
        flang = lang
    if fformat is None:
        fformat = format
    if flang.l in ("en", "fr"):
        return f"{to_sentence_case(get_var_l10n(ddict["lang"][to_say.l], "name", fformat, flang), flang)} ({get_var_l10n(ddict["region"][f"{to_say.t}".lower()], "name", fformat, flang)})"


def self_close(fformat: str | None = None) -> str:
    if fformat is None:
        fformat = format
    if fformat == "H":
        return ">"
    elif fformat == "X":
        return "/>"
    else:
        raise ValueError("`self_close` format is not `H` or `X`")


#def validate_data()->None:
#    sys.stderr.write("Validating data…")
#    start_time=time.perf_counter()
#    for key in data:
#        if not unicodedata.is_normalized("NFC",key):
#            raise SystemExit("Key name not normalized in NFC")
#    for value in data.values():
#        if isinstance(value,str):
#            if not unicodedata.is_normalized("NFC",value):
#                raise SystemExit("String not normalized in NFC")
#    end_time=time.perf_counter()
#    sys.stderr.write(f"\rValidated data in {end_time-start_time:.3f}\xa0s\n")


SCRIPT: Path = Path(__file__).resolve()
GABEL: Path = SCRIPT.parent
DICTS: Path = Path(GABEL)/"dicts"
INDEX: Path = Path(GABEL)/".."/"i"

data: dict = {}

if __name__ == "__main__":
    sys.stderr.write("Loading data…")
    data_start_time = time.perf_counter()

item_files: list[Path] = [
    path
    for path in Path(INDEX).rglob("data.json")
    if path.is_file()
]

ddict: dict = {}

for dictionary in ["disclaim", "lang", "license", "month", "region", "script",
                   "share", "string", "validate", "weekday"]:
    with open(Path(DICTS)/f"{dictionary}.json", "r", encoding="utf-8") as f:
        ddict[dictionary] = json.load(f)

for item_file in item_files:
    with open(item_file, "r", encoding="utf-8") as f:
        obj = json.load(f)
        obj_id = obj.get("id")
        data[obj_id] = obj

if __name__ == "__main__":
    data_end_time = time.perf_counter()
    sys.stderr.write(f"\rLoaded data in {data_end_time-data_start_time:.3f}\xa0s\n")

    sys.stderr.write("Generating pages…")
    start_time = time.perf_counter()

    # TODO: Make this a function(s); these variables are global.
    for item_file in item_files:
        i: str = get_i(item_file)

        if data[i]["type"] != "comic_page":
            continue

        for lang in data[i]["langs"]:
            lang: L = L.get(lang)
            format: str = "H"

            canonical: str = f"https://gabl.ink/i/{i}/{f"{lang}".lower()}/"

            F: list[str] = ["<!DOCTYPE html>\n"]

            if data[i].get("copyright", {}).get("license"):
                F.append("<!-- SPDX-License-Identifier: ")
                spdx_license_count: int = len(data[i]["copyright"]["license"])
                spdx_license_num: int = 1
                for license in data[i]["copyright"]["license"]:
                    F.append(ddict["license"][license]["spdx"])
                    if spdx_license_num < spdx_license_count:
                        F.append(" OR ")
                        spdx_license_num += 1
                F.append(" -->\n")

            lang_dir: str
            if lang.s:
                lang_dir = ddict["script"][lang.s]["dir"]
            elif ddict["lang"][lang.l].get("script"):
                lang_dir = ddict["script"][ddict["lang"][lang.l]["script"]]["dir"]
            else:
                lang_dir = "auto"

            # TODO: I don’t think this always works
            if data.get("config",{}).get("config",{}).get("relative_paths") is True:
                if i == "root":
                    styles: str = "../gabel/styles"
                else:
                    depth: int = i.count("/") + 2
                    styles: list[str] = ["../"]
                    for d in range(depth):
                        styles.append("../")
                    styles.append("gabel/styles")
                    styles: str = "".join(styles)
            else:
                styles: str = "/gabel/styles"

            F.append(
                f"<html lang={lang} dir={lang_dir} itemscope itemtype=https://schema.org/WebPage>"

                f"<meta charset=utf-8{self_close()}"
                f'<meta name=viewport content="width=device-width,initial-scale=1"{self_close()}'

                f"<title>{msg_l10n(get_var_l10n(data[i], "title", "t"), string="html_title")}</title>"

                f"<meta name=description content{attr(get_var_l10n(data[i], "description", "t"))}{self_close()}"

                f"<meta name=robots content=index,follow{self_close()}"

                f"<link rel=canonical href={canonical} hreflang={lang} type=text/html{self_close()}"

                # TODO: `if type != comic_page` (sh:349)

                f"<link rel=stylesheet href={styles}/mul.css hreflang=zxx{self_close()}"
                f"<link rel=stylesheet href={styles}/{lang.l}.css hreflang=zxx{self_close()}"
                f"<link rel=stylesheet href={styles}/comic_page.css hreflang=zxx{self_close()}"

                f'<link rel="external license" href{attr(get_var_l10n(ddict["license"][data[i]["copyright"]["license"][0]], "url", "i"))}{self_close()}'

                # TODO: Prefetches (starting at sh:420)

                f"<meta property=og:type content=article{self_close()}"
                f"<meta property=og:title content{attr(get_var_l10n(data[i], "title", "t"))}{self_close()}"
                f"<meta property=og:description content{attr(get_var_l10n(data[i], "description", "t"))}{self_close()}"
                f"<meta property=og:site_name content=gabl.ink{self_close()}"
                f"<meta property=og:url content={canonical}{self_close()}"
                f"<meta property=og:image content={canonical}image.png{self_close()}"
                # TODO: video_exists (sh:322–332, sh:454)
                f"<meta property=og:locale content={lang.l}_{lang.t}{self_close()}"

                "<script type=application/ld+json>{"
                '"@context":"https://schema.org",'
                '"@type":"WebPage"'
                "}</script>"

                "<header>"
                "<a href=https://gabl.ink/ id=gabldotink_logo>gabl.ink</a>"

                "<ul id=L>"
            )
            for l in sorted(data[i]["langs"]):
                l: L = L.get(l)
                F.append(language_list_entry(l))
            F.append(
                "</ul></header>"

                f"<h1>{msg_l10n(get_var_l10n(data[i], "title"), string="page_title_html")}</h1>"

                "<nav class=N>"

                f"{make_nav_button("f")}"
                f"{make_nav_button("p")}"
                f"{make_nav_button("n")}"
                f"{make_nav_button("l")}"

                "</nav>"
            )

            if Path(INDEX/i/f"{lang}".lower()/"video.webm").is_file():
                F.append(
                    "<video id=M controls poster=image.png preload=auto>"
                    f"<source src=video.webm type=video/webm{self_close()}"
                )
                if Path(INDEX/i/f"{lang}".lower()/"subs.vtt").is_file():
                    F.append(
                        f"<track default src=subs.vtt srclang={lang} kind=subtitles "
                        f"label{attr(say_lang(lang, "t"))}{self_close()}"
                    )
                if Path(INDEX/i/f"{lang}".lower()/"cc.vtt").is_file():
                    F.append(
                        f"<track src=cc.vtt srclang={lang} kind=captions "
                        f"label{attr(f"{say_lang(lang, "t")}{msg_l10n(string="cc")}")}{self_close()}"
                    )
                F.append(
                    "<p>"
                    f"{msg_l10n(lang, get_var_l10n(data[data[i]["location"]["series"]], "title", "t"), get_var_l10n(data[i], "title", "t"), get_var_l10n(data[i], "title", "t"), string="video_not_supported")}"
                    "</p></video>"
                )
            elif Path(INDEX/i/f"{lang}".lower()/"image.png").is_file():
                F.append("<picture id=M")
                if get_var_l10n(data[i], "tooltip") is not None:
                    F.append(f" title{attr(get_var_l10n(data[i], "tooltip", "t"))}")
                F.append(
                    ">"
                    f"<img src=image.png fetchpriority=high alt{attr(msg_l10n(string="see_transcript"))}{self_close()}"
                    "</picture>"
                )

            F.append(
                "<nav class=N>"

                f"{make_nav_button("f")}"
                f"{make_nav_button("p")}"
                f"{make_nav_button("n")}"
                f"{make_nav_button("l")}"

                "</nav><nav><details><summary>"
            )

            # TODO: Support multiple container depths

            F.append(
                f"{msg_l10n(get_var_l10n(data[data[i]["location"]["series"]], "title"), string="series_title_html")}"
                f"{msg_l10n(data[i]["location"]["page"], string="comma_page")}"
                f"{msg_l10n(get_var_l10n(data[i], "title"), string="page_title_html")}"
                "</summary></details></nav>"

            # TODO: Page list

                "<details>"
                f"<summary><h2>{msg_l10n(string="transcript_name")}</h2></summary>"
                "<table id=T>"
            )

            for line in data[i]["transcript"]:
                # TODO: Check encyclopedia item type
                #line_h_type=data[f"encyclopedia/{line["H"]}"]["type"]
                F.append(
                    "<tr>"
                    "<th scope=row>"
                )
                line_h_label: str
                if data[f"encyclopedia/{line["H"]}"].get("name", {}).get("label"):
                    line_h_label = get_var_l10n(data[f"encyclopedia/{line["H"]}"].get("name", {}), "label")
                else:
                    line_h_label = get_var_l10n(data[f"encyclopedia/{line["H"]}"].get("name", {}), "label")
                F.append(
                    f"{line_h_label}"
                    f"{close_tag("th")}"
                    "<td>"
                )
                F.append(get_var_l10n(line, "d"))
                F.append(
                    f"{close_tag("td")}"
                    f"{close_tag("tr")}"
                )
            F.append(
                "</table></details><hr>"
                f"<h2>{msg_l10n(string="log")}</h2>"
            )

            for entry in data[i]["log"]:
                F.append(
                    f"<article id=log_{print_date(date.fromisoformat(entry["date"]))}><details>"
                    f"<summary><h3>{say_date(date.fromisoformat(entry["date"]))}</h3></summary>"
                )
                for line in entry["content"]:
                    if text_to_html(get_var_l10n(line, "p", "t")) == get_var_l10n(line, "p"):
                        F.append("<p>")
                    F.append(get_var_l10n(line, "p"))
                F.append("</details></article>")

            F.append(
                "<hr>"
                "<p id=canonical_url>"
                f"{msg_l10n(canonical, string="canonical_url")}"
                f"<a href={canonical} hreflang={lang} type=text/html>"
                f"{canonical}"
                "</a>"

                "<details id=share_links>"
                f"<summary>{msg_l10n(string="share_this_page")}</summary>"
                "<ul></ul></details>"

                "<details id=validate_links>"
                f"<summary>{msg_l10n(string="validate_this_page")}</summary>"
                "<ul></ul></details>"

                "<footer><p><span class=w>"
                f"{msg_l10n(string="copyright_notice")}"
                f"{data[i]["copyright"]["year"]["first"]}"
            )
            if data[i]["copyright"]["year"].get("last"):
                F.append(
                    f"{msg_l10n(string="copyright_year_separator")}"
                    f"{data[i]["copyright"]["year"]["last"]}"
                )
            F.append(
                "</span> "
                f"<span translate{attr("no")}>gabl.ink</span>"

                f"<p>{msg_l10n(string="license")}"
                '<a rel="external license" href'
                f"{attr(get_var_l10n(ddict["license"][data[i]["copyright"]["license"][0]], "url", "i"))}"
                ">"
                f"{get_var_l10n(ddict["license"][data[i]["copyright"]["license"][0]], "title")}"
            )
            if ddict["license"][data[i]["copyright"]["license"][0]].get("abbr"):
                F.append(msg_l10n(get_var_l10n(ddict["license"][data[i]["copyright"]["license"][0]], "abbr"), string="copyright_license_abbr"))
            F.append("</a>")

            if data[i].get("disclaimer"):
                F.append("<p>")
                if len(data[i]["disclaimer"]) == 1:
                    F.append(
                        f"{msg_l10n(string="disclaimer")}"
                        f"{get_var_l10n(ddict["disclaim"][data[i]["disclaimer"][0]], "text")}"
                    )
                else:
                    F.append(
                        f"{msg_l10n(string="disclaimer_plural")}"
                        "<ul class=horizontal_list>"
                    )
                    for d in data[i]["disclaimer"]:
                        F.append(
                            "<li><p>"
                            f"{get_var_l10n(ddict["disclaim"][d], "text")}"
                        )
                    F.append("</ul>")

            F.append(
                "</footer>"
                f"{close_tag("body")}"
                f"{close_tag("html")}"
                "\n"
            )

            F: str = "".join(F)

            output_file_path: Path = Path(INDEX)/i/f"{lang}".lower()/"index.html"
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            output_file_path.touch()

            with open(output_file_path, "r+", encoding="utf-8", newline="") as output_file:
                # Only write if there is a change
                if F != output_file.read():
                    output_file.seek(0)
                    output_file.truncate()
                    output_file.write(F)
    end_time = time.perf_counter()
    sys.stderr.write(f"\rGenerated pages in {end_time-start_time:.3f}\xa0s\n")

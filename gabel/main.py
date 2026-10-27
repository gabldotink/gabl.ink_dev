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
                 v: list | None = None, x: str | None = None):
        self.l: str = l
        self.s: str | None = s
        self.t: str | None = t
        self.v: list | None = v
        self.x: str | None = x

    @classmethod
    def make(cls, l: str, s: str | None = None, t: str | None = None,
             v: list | None = None, x: str | None = None) -> "L":
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

        r: list = [self.l]

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


def attribute_string(string: str) -> str:
    """Takes a plain text string as input and returns the HTML
    component that comes right after the attribute name. Returns an
    empty string if the input is empty. Returns the equals sign,
    quotation marks as appropriate, and the string with characters
    escapes as necessary if the input is not empty.

    >>> attribute_string("")
    ''
    >>> attribute_string("hello, world")
    '="hello, world"'
    >>> attribute_string("&")
    '=&'
    >>> attribute_string("&amp;")
    '=&amp;amp;'
    >>> attribute_string("'")
    '="\\'"'
    >>> attribute_string('"')
    '=\\'"\\''
    """
    if not isinstance(string, str):
        raise TypeError("Not a string")

    # In HTML5, `attribute` is equivalent to `attribute=""`
    if not string:
        return ""

    quoted: bool

    if any(c in string for c in " \"'=<>`\n\r\t\v\f"):
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


def expand_parts(parts: list) -> list:
    """Returns a list of integers from a `parts` list.

    >>> expand_parts([1, 2, 3])
    [1, 2, 3]
    >>> expand_parts(["1-3"])
    [1, 2, 3]
    >>> expand_parts([4, 7, "1-5"])
    [1, 2, 3, 4, 5, 7]
    """
    result: set = set()

    for part in parts:
        if isinstance(part, int):
            result.add(part)
        else:
            start, end = map(int, part.split("-"))
            result.update(range(start, end + 1))

    return sorted(result)


def get_i_id(i: Path) -> str:
    with open(i, "r", encoding="utf-8") as f:
        item_obj = json.load(f)
        return item_obj["id"]


def get_var_l10n(index, key: str, format: str, l10n_lang: L) -> str:
    # e.g. get_var_l10n(data["jrco_beta/1"]["location"], "series", "t", lang)

    formats: str = "AHiLptx"
    real_formats: str = "HiLpt"
    options: list[str] = [f"{l10n_lang}", l10n_lang.l, "mul", "zxx", "z"]

    if format not in real_formats:
        raise ValueError("Invalid real format given")

    def _find_equals(pointer: str) -> str:
        to_find: tuple = index[key][o][f"{pointer}e"].rpartition("_")

        # TODO: catch invalid equals
        if to_find[2] and to_find[2] not in formats:
            raise ValueError("Equals does not contain a valid format")
        elif to_find[2] and not to_find[1]:
            return get_var_l10n(index, key, to_find[2], l10n_lang)
        elif to_find[0] and not to_find[1]:
            return get_var_l10n(index, key, format, to_find[0])
        else:
            return get_var_l10n(index, key, to_find[2], to_find[0])

    # ASCII

    # HTML5
    if format == "H":
        for o in options:
            if o == "z":
                return ""

            to_check: dict = index.get(key, {}).get(o, {})

            if "H" in to_check:
                return to_check["H"]
            elif "He" in to_check:
                return _find_equals("H")
            elif "t" in to_check:
                return text_to_html(to_check["t"])
            elif "te" in to_check:
                return text_to_html(_find_equals("t"))
            elif "A" in to_check:
                return to_check["A"]
            elif "Ae" in to_check:
                return _find_equals("A")
            elif "e" in to_check:
                return get_var_l10n(index, key, format,
                                    L.get(to_check["e"]))
    # identifier
    elif format == "i":
        for o in options:
            if o == "z":
                return ""

            to_check: dict = index.get(key, {}).get(o, {})
            
            if "i" in to_check:
                return to_check["i"]
            elif "ie" in to_check:
                return _find_equals("i")
            elif "e" in to_check:
                return get_var_l10n(index, key, format,
                                    L.get(to_check["e"]))
    # LaTeX
    elif format == "L":
        for o in options:
            if o == "z":
                return ""
                    
            to_check: dict = index.get(key, {}).get(o, {})

            if "L" in to_check:
                return to_check["L"]
            elif "Le" in to_check:
                return _find_equals("L")
            elif "x" in to_check:
                return to_check("x")
            elif "xe" in to_check:
                return _find_equals("x")
            elif "t" in to_check:
                return text_to_latex(to_check["t"])
            elif "te" in to_check:
                return text_to_latex(_find_equals("t"))
            elif "e" in to_check:
                return get_var_l10n(index, key, format,
                                    L.get(to_check["e"]))
    # print
    elif format == "p":
        for o in options:
            if o == "z":
                return ""
            
            to_check: dict = index.get(key, {}).get(o, {})

            if "p" in to_check:
                return to_check["p"]
            elif "pe" in to_check:
                return _find_equals("p")
            elif "t" in to_check:
                return to_check["t"]
            elif "te" in to_check:
                _find_equals("t")
            elif "A" in to_check:
                return to_check["A"]
            elif "Ae" in to_check:
                return _find_equals("A")
            elif "e" in to_check:
                return get_var_l10n(index, key, format,
                                    L.get(to_check["e"]))
    # text
    elif format == "t":
        for o in options:
            if o == "z":
                return ""

            to_check: dict = index.get(key, {}).get(o, {})

            if "t" in to_check:
                return to_check["t"]
            elif "te" in to_check:
                return _find_equals("t")
            elif "A" in to_check:
                return to_check["A"]
            elif "Ae" in to_check:
                return _find_equals("A")
            elif "e" in to_check:
                return get_var_l10n(index, key, format,
                                    L.get(to_check["e"]))
    # TeX


def id_base(i: str) -> str:
    """Returns the base part of an ID.

    >>> id_base("foo")
    'foo'
    >>> id_base("foo/bar")
    'bar'
    >>> id_base("foo/bar/baz")
    'baz'
    """
    if "/" in i:
        return i.rpartition("/")[2]
    else:
        return i


def id_parent(i: str) -> str | None:
    """Returns the non‐base part of an ID.

    >>> id_parent("foo")

    >>> id_parent("foo/bar")
    'foo'
    >>> id_parent("foo/bar/baz")
    'foo/bar'
    """
    if "/" in i:
        return i.rpartition("/")[0]
    else:
        return None


def language_list_entry(l: L) -> str:
    r: list = ["<li"]

    if l.t is not None:
        r.append(
            f''' style="list-style-type:'{to_regional_indicators(l.t)} '"'''
            ">"
        )

    if f"{l}" == f"{lang}":
        r.append("<b>")
    else:
        r.append(f'<a lang={l} href=../{f"{l}".lower()}/ hreflang={l}>')

    r.append(say_lang(l, "H"))

    if f"{l}" == f"{lang}":
        r.append("</b>")
    else:
        r.append("</a>")

    return "".join(r)


def make_nav_button(button: str, lang: L) -> str:
    button_arrow, button_id, button_fl = {
        "f": ("⇦", "first", "first"),
        "p": ("←", "prev", "first"),
        "n": ("→", "next", "last"),
        "l": ("⇨", "last", "last"),
    }[button]

    r: list[str] = ["<div class=B title"]

    if (
        data[i_id]["location"]["page"]
        == data[data[i_id]["location"]["series"]].get(button_fl)
    ):
        r.append(
            f'{attribute_string(msg_l10n(msg_l10n(lang=lang, string=f"nav_button_{button_id}_inline"), lang=lang, string="this_is_x_page"))}'
            ">"
        )
    else:
        if button in ("f", "l"):
            r.append(attribute_string(msg_l10n(get_var_l10n(data[f'{data[i_id]["location"]["series"]}/{data[data[i_id]["location"]["series"]][button_id]}'], "title", "t", lang), lang=lang, string="nav_button_page_title")))
        elif button in ("p", "n"):
            r.append(attribute_string(msg_l10n(get_var_l10n(data[f'{data[i_id]["location"]["series"]}/{data[i_id]["location"][button_id]}'], "title", "t", lang), lang=lang, string="nav_button_page_title")))
        r.append("><a href=../../")
        if button in ("f", "l"):
            r.append(f'{data[data[i_id]["location"]["series"]][button_id]}')
        elif button in ("p", "n"):
            r.append(f'{data[i_id]["location"][button_id]}')
        r.append(f'/{f"{lang}".lower()}/ hreflang={lang}>')

    r.append(f'<span class=A aria-hidden=true>{button_arrow}</span><br>{msg_l10n(lang=lang, string=f"nav_button_{button_id}")}')

    if (
        data[i_id]["location"]["page"]
        != data[data[i_id]["location"]["series"]].get(button_fl, {})
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


def msg_l10n(*args, lang: L, string: str) -> str:
    return get_var_l10n(ddict["string"], string, "p",
                        lang).format(*args)


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

    >>> to_regional_indicators("HELLOWORLD")
    '🇭🇪🇱🇱🇴🇼🇴🇷🇱🇩'
    >>> to_regional_indicators("US")
    '🇺🇸'
    """
    out_chars: list[str] = []
    for ch in string:
        out_chars.append(chr(0x1f1e6+(ord(ch)-65)))
    return "".join(out_chars)


def to_sentence_case(string: str, lang: L) -> str:
    """Capitalizes the first character of a string as appropriate for
    the language.

    >>> to_sentence_case("toki pona", L.get("tok"))
    'toki pona'
    >>> to_sentence_case("français", L.get("fr"))
    'Français'
    """
    if lang.l == "tok":
        return string
    else:
        return f"{string[:1].upper()}{string[1:]}"


# The shell script supports negative years, but `datetime` does not.
def say_date(d: date, lang: L) -> str:
    """Returns word form of date in HTML format.

    >>> say_date(date.fromisoformat("19971225"), L.get("en-US"))
    '<time datetime=1997-12-25>December\xa025, 1997</time>'
    >>> say_date(date.fromisoformat("19971225"), L.get("en-GB"))
    '<time datetime=1997-12-25>25\xa0December 1997</time>'
    >>> say_date(date.fromisoformat("20220401"), L.get("fr"))
    '<time datetime=2022-04-01>1er\xa0avril 2022</time>'
    """
    r: list[str] = [f"<time datetime={print_date(d)}>"]

    ad: bool

    if d.year > 0 and d.year < 1000:
        ad = True
    else:
        ad = False

    if lang.l == "en":
        if lang.t == "US":
            r.append(
                f'{get_var_l10n(ddict["month"]["months"][d.month-1], "name", "H", lang)}'
                f"\xa0{d.day}, "
            )
        elif lang.t == "GB":
            r.append(
                f"{d.day}\xa0"
                f'{get_var_l10n(ddict["month"]["months"][d.month-1], "name", "H", lang)}'
                " "
            )
        if ad:
            r.append("AD\xa0")
        r.append(f"{d.year}")
    elif lang.l == "fr":
        if d.day == 1:
            r.append("1er")
        else:
            r.append(f"{d.day}")
        r.append(
            "\xa0"
            f'{get_var_l10n(ddict["month"]["months"][d.month-1], "name", "H", lang)}'
        )
        if ad:
            r.append(f"{d.year}\xa0ap.\xa0J.‑C.")
        r.append(f" {d.year}")
    elif lang.l == "es":
        r.append(
            f"{d.day}\xa0de\xa0"
            f'{get_var_l10n(ddict["month"]["months"][d.month-1], "name", "H", lang)}'
            " de "
        )
        if ad:
            r.append(f'{d.year}\xa0d.\xa0C.')
        r.append(f"{d.year}")
    elif lang.l in ("ja", "ko", "zh"):
        r.append(
            f'{d.year}{msg_l10n(lang=lang, string="say_date_cjk_year")}'
            f'{d.month}{msg_l10n(lang=lang, string="say_date_cjk_month")}'
            f'{d.day}{msg_l10n(lang=lang, string="say_date_cjk_day")}'
        )

    r.append("</time>")

    return "".join(r)


def say_lang(lang: L, format: str) -> str:
    """Returns a formatted language name and region.

    >>> say_lang(L.get("en-US"), "t")
    'English (United States)'
    >>> say_lang(L.get("fr-FR"), "t")
    'Français (France)'
    """
    if lang.l in ("en", "fr"):
        return f'{to_sentence_case(get_var_l10n(ddict["lang"][lang.l], "name", format, lang), lang)} ({get_var_l10n(ddict["region"][f"{lang.t}".lower()], "name", format, lang)})'


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

    sys.stderr.write("Generating HTML pages…")
    start_time = time.perf_counter()

    # TODO: Make this a function(s); these variables are global.
    for i in item_files:
        i_id: str = get_i_id(i)

        if data[i_id]["type"] != "comic_page":
            continue

        for lang in data[i_id]["langs"]:
            lang: L = L.get(lang)

            canonical: str = f'https://gabl.ink/i/{i_id}/{f"{lang}".lower()}/'

            F: list[str] = ["<!DOCTYPE html>\n"]

            if data[i_id].get("copyright", {}).get("license"):
                F.append("<!-- SPDX-License-Identifier: ")
                spdx_license_count = len(data[i_id]["copyright"]["license"])
                spdx_license_num = 1
                for license in data[i_id]["copyright"]["license"]:
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

            # TODO: Only works for one type of depth, but I want to redesign that whole system anyway (sh:349–385)
            styles: str = "../../../../gabel/styles"

            F.append(
                f"<html lang={lang} dir={lang_dir} itemscope itemtype=https://schema.org/WebPage>"

                '<meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">'

                f'<title>{msg_l10n(get_var_l10n(data[i_id], "title", "t", lang), lang=lang, string="html_title")}</title>'

                f'<meta name=description content{attribute_string(get_var_l10n(data[i_id], "description", "t", lang))}>'

                "<meta name=robots content=index,follow>"

                f"<link rel=canonical href={canonical} hreflang={lang} type=text/html>"

                # TODO: `if type != comic_page` (sh:349)

                f"<link rel=stylesheet href={styles}/{lang.l}.css hreflang=zxx>"
                f"<link rel=stylesheet href={styles}/comic_page.css hreflang=zxx>"

                f'<link rel="external license" href{attribute_string(get_var_l10n(ddict["license"][data[i_id]["copyright"]["license"][0]], "url", "i", lang))}>'

                # TODO: Prefetches (starting at sh:420)

                "<meta property=og:type content=article>"
                f'<meta property=og:title content{attribute_string(get_var_l10n(data[i_id], "title", "t", lang))}>'
                f'<meta property=og:description content{attribute_string(get_var_l10n(data[i_id], "description", "t", lang))}>'
                "<meta property=og:site_name content=gabl.ink>"
                f"<meta property=og:url content={canonical}>"
                f"<meta property=og:image content={canonical}image.png>"
                # TODO: video_exists (sh:322–332, sh:454)
                f"<meta property=og:locale content={lang.l}_{lang.t}>"

                "<script type=application/ld+json>{"
                '"@context":"https://schema.org",'
                '"@type":"WebPage"'
                "}</script>"

                "<header>"
                "<a href=https://gabl.ink/ id=gabldotink_logo>gabl.ink</a>"

                "<ul id=L>"
            )
            for l in sorted(data[i_id]["langs"]):
                l: L = L.get(l)
                F.append(language_list_entry(l))
            F.append(
                "</ul></header>"

                f'<h1>{msg_l10n(get_var_l10n(data[i_id], "title", "H", lang), lang=lang, string="page_title_html")}</h1>'

                "<nav class=N>"

                f'{make_nav_button("f", lang)}'
                f'{make_nav_button("p", lang)}'
                f'{make_nav_button("n", lang)}'
                f'{make_nav_button("l", lang)}'

                "</nav>"
            )

            if Path(INDEX/i_id/f"{lang}".lower()/"video.webm").is_file():
                F.append(
                    "<video id=M controls poster=image.png preload=auto>"
                    "<source src=video.webm type=video/webm>"
                )
                if Path(INDEX/i_id/f"{lang}".lower()/"subs.vtt").is_file():
                    F.append(
                        f"<track default src=subs.vtt srclang={lang} kind=subtitles "
                        f'label{attribute_string(say_lang(lang, "t"))}>'
                    )
                if Path(INDEX/i_id/f"{lang}".lower()/"cc.vtt").is_file():
                    F.append(
                        f"<track src=cc.vtt srclang={lang} kind=captions "
                        f'''label{attribute_string(f'{say_lang(lang, "t")}{msg_l10n(lang=lang, string="cc")}')}>'''
                    )
                F.append(
                    "<p>"
                    f'{msg_l10n(lang, get_var_l10n(data[data[i_id]["location"]["series"]], "title", "t", lang), get_var_l10n(data[i_id], "title", "t", lang), get_var_l10n(data[i_id], "title", "t", lang), lang=lang, string="video_not_supported")}'
                    "</p></video>"
                )
            elif Path(INDEX/i_id/f"{lang}".lower()/"image.png").is_file():
                F.append("<picture id=M")
                if get_var_l10n(data[i_id], "tooltip", "H", lang) is not None:
                    F.append(f' title{attribute_string(get_var_l10n(data[i_id], "tooltip", "t", lang))}')
                F.append(
                    ">"
                    f'<img src=image.png fetchpriority=high alt{attribute_string(msg_l10n(lang=lang, string="see_transcript"))}>'
                    "</picture>"
                )

            F.append(
                "<nav class=N>"

                f'{make_nav_button("f", lang)}'
                f'{make_nav_button("p", lang)}'
                f'{make_nav_button("n", lang)}'
                f'{make_nav_button("l", lang)}'

                "</nav><nav><details><summary>"
            )

            # TODO: Support multiple container depths

            F.append(
                f'{msg_l10n(get_var_l10n(data[data[i_id]["location"]["series"]], "title", "H", lang), lang=lang, string="series_title_html")}'
                f'{msg_l10n(data[i_id]["location"]["page"], lang=lang, string="comma_page")}'
                f'{msg_l10n(get_var_l10n(data[i_id], "title", "H", lang), lang=lang, string="page_title_html")}'
                "</summary></details></nav>"

            # TODO: Page list

                "<details>"
                f'<summary><h2>{msg_l10n(lang=lang, string="transcript_name")}</h2></summary>'
                "<table id=T>"
            )

            for line in data[i_id]["transcript"]:
                # TODO: Check encyclopedia item type
                #line_h_type=data[f'encyclopedia/{line["H"]}']["type"]
                F.append(
                    "<tr>"
                    "<th scope=row>"
                )
                line_h_label: str
                if data[f'encyclopedia/{line["H"]}'].get("name", {}).get("label"):
                    line_h_label = get_var_l10n(data[f'encyclopedia/{line["H"]}'].get("name", {}), "label", "H", lang)
                else:
                    line_h_label = get_var_l10n(data[f'encyclopedia/{line["H"]}'].get("name", {}), "label", "H", lang)
                F.append(
                    f"{line_h_label}"
                    "<td>"
                )
                if get_var_l10n(line, "d", "t", lang) == get_var_l10n(line, "d", "H", lang):
                    F.append("<p>")
                F.append(get_var_l10n(line, "d", "H", lang))
            F.append(
                "</table></details><hr>"
                f'<h2>{msg_l10n(lang=lang, string="log")}</h2>'
            )

            for entry in data[i_id]["log"]:
                F.append(
                    f'<article id=log_{print_date(date.fromisoformat(entry["date"]))}><details>'
                    f'<summary><h3>{say_date(date.fromisoformat(entry["date"]), lang)}</h3></summary>'
                )
                for line in entry["content"]:
                    if text_to_html(get_var_l10n(line, "p", "t", lang)) == get_var_l10n(line, "p", "H", lang):
                        F.append("<p>")
                    F.append(get_var_l10n(line, "p", "H", lang))
                F.append("</details></article>")

            F.append(
                "<hr>"
                "<p id=canonical_url>"
                f'{msg_l10n(canonical, lang=lang, string="canonical_url")}'
                f"<a href={canonical} hreflang={lang} type=text/html>"
                f"{canonical}"
                "</a>"

                "<details id=share_links>"
                f'<summary>{msg_l10n(lang=lang, string="share_this_page")}</summary>'
                "<ul></ul></details>"

                "<details id=validate_links>"
                f'<summary>{msg_l10n(lang=lang, string="validate_this_page")}</summary>'
                "<ul></ul></details>"

                "<footer><p><span class=w>"
                f'{msg_l10n(lang=lang, string="copyright_notice")}'
                f'{data[i_id]["copyright"]["year"]["first"]}'
            )
            if data[i_id]["copyright"]["year"].get("last"):
                F.append(
                    f'{msg_l10n(lang=lang, string="copyright_year_separator")}'
                    f'{data[i_id]["copyright"]["year"]["last"]}'
                )
            F.append(
                "</span> "
                "<span translate=no>gabl.ink</span>"

                f'<p>{msg_l10n(lang=lang, string="license")}'
                '<a rel="external license" href'
                f'{attribute_string(get_var_l10n(ddict["license"][data[i_id]["copyright"]["license"][0]], "url", "i", lang))}'
                ">"
                f'{get_var_l10n(ddict["license"][data[i_id]["copyright"]["license"][0]], "title", "H", lang)}'
            )
            if ddict["license"][data[i_id]["copyright"]["license"][0]].get("abbr"):
                F.append(msg_l10n(get_var_l10n(ddict["license"][data[i_id]["copyright"]["license"][0]], "abbr", "H", lang), lang=lang, string="copyright_license_abbr"))
            F.append("</a>")

            if data[i_id].get("disclaimer"):
                F.append("<p>")
                if len(data[i_id]["disclaimer"]) == 1:
                    F.append(
                        f'{msg_l10n(lang=lang, string="disclaimer")}'
                        f'{get_var_l10n(ddict["disclaim"][data[i_id]["disclaimer"][0]], "text", "H", lang)}'
                    )
                else:
                    F.append(
                        f'{msg_l10n(lang=lang, string="disclaimer_plural")}'
                        "<ul class=horizontal_list>"
                    )
                    for d in data[i_id]["disclaimer"]:
                        F.append(
                            "<li><p>"
                            f'{get_var_l10n(ddict["disclaim"][d], "text", "H", lang)}'
                        )
                    F.append("</ul>")

            F.append("</footer>\n")

            output: str = "".join(F)

            output_file_path: Path = Path(INDEX)/i_id/f"{lang}".lower()/"index.html"
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            output_file_path.touch()

            with open(output_file_path, "r+", encoding="utf-8", newline="") as output_file:
                # Only write if there is a change
                if output != output_file.read():
                    output_file.seek(0)
                    output_file.truncate()
                    output_file.write(output)
    end_time = time.perf_counter()
    sys.stderr.write(f"\rGenerated HTML pages in {end_time-start_time:.3f}\xa0s\n")

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
                if re.fullmatch(r"^[a-z]{2,3}$", subtag):
                    langdata["l"] = subtag
                    it += 1
                else:
                    raise ValueError("Invalid language code")
            elif it <= 2:
                if re.fullmatch(r"^[A-Z][a-z]{3}$", subtag):
                    if not langdata.get("t"):
                        langdata["s"] = subtag
                    else:
                        raise ValueError("Invalid language code")
                elif re.fullmatch(r"^[A-Z]{2}$|^[0-9]{3}$", subtag):
                    langdata["t"] = subtag
                elif re.fullmatch(r"^[a-z]{5,8}$|^[0-9][a-z0-9]{3}$", subtag):
                    if not langdata.get("v"):
                        langdata["v"] = [subtag]
                    else:
                        langdata["v"].append(subtag)
                elif subtag == "x":
                    langdata["x"] = "-".join(subtags[it+1:])
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

    options: list[str] = [f"{l10n_lang}", l10n_lang.l, "mul", "zxx", "x"]

    if format == "i":
        for o in options:
            if o == "x":
                return ""
            elif "i" in index.get(key, {}).get(o, {}):
                return index[key][o]["i"]
            elif "e" in index.get(key, {}).get(o, {}):
                return get_var_l10n(index, key, format,
                                    L.get(index[key][o]["e"]))
    elif format == "p":
        for o in options:
            if o == "x":
                return ""
            elif "p" in index.get(key, {}).get(o, {}):
                return index[key][o]["p"]
            elif "t" in index.get(key, {}).get(o, {}):
                return index[key][o]["t"]
            elif "e" in index.get(key, {}).get(o, {}):
                return get_var_l10n(index, key, format,
                                    L.get(index[key][o]["e"]))
    elif format == "t":
        for o in options:
            if o == "x":
                return ""
            elif "t" in index.get(key, {}).get(o, {}):
                return index[key][o]["t"]
            elif "e" in index.get(key, {}).get(o, {}):
                return get_var_l10n(index, key, format,
                                    L.get(index[key][o]["e"]))
    elif format == "h":
        for o in options:
            if o == "x":
                return ""
            elif "h" in index.get(key, {}).get(o, {}):
                return index[key][o]["h"]
            elif "t" in index.get(key, {}).get(o, {}):
                return text_to_html(index[key][o]["t"])
            elif "e" in index.get(key, {}).get(o, {}):
                return get_var_l10n(index, key, format,
                                    L.get(index[key][o]["e"]))


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
            f''' style="list-style-type:'{to_regional_indicators(l.t)} '"''')
    r.append(">")

    if f"{l}" == f"{lang}":
        r.append("<b>")
    else:
        r.append(f'<a lang={l} href=../{f"{l}".lower()}/ hreflang={l}>')

    r.append(say_lang(l, "h"))

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

    r: list[str] = ["<div class=nav_button title"]

    if (
        data[i_id]["location"]["page"]
        == data[data[i_id]["location"]["series"]].get(button_fl)
    ):
        r.append(attribute_string(msg_l10n(msg_l10n(lang=lang, string=f"nav_button_{button_id}_inline"), lang=lang, string="this_is_x_page")))
        r.append(">")
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

    r.append(f'<span class=nav_button_arrow aria-hidden=true>{button_arrow}</span><br>{msg_l10n(lang=lang, string=f"nav_button_{button_id}")}')

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
#        if data["dictionaries/share_link"][name].get(key, {}).get("key"):
#            pass
#
#    r.append(data["dictionaries/share_link"][name]["base"])


def msg_l10n(*args, lang: L, string: str) -> str:
    return get_var_l10n(data["dictionaries/string"]["dictionary"], string, "p",
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
            r.append(get_var_l10n(data["dictionaries/month"]["dictionary"]
                                  ["months"][d.month-1], "name", "h", lang))
            r.append(f"\xa0{d.day}, ")
        elif lang.t == "GB":
            r.append(f"{d.day}\xa0")
            r.append(get_var_l10n(data["dictionaries/month"]["dictionary"]
                                  ["months"][d.month-1], "name", "h", lang))
            r.append(" ")
        if ad:
            r.append("AD\xa0")
        r.append(f"{d.year}")
    elif lang.l == "fr":
        if d.day == 1:
            r.append("1er")
        else:
            r.append(f"{d.day}")
        r.append("\xa0")
        r.append(get_var_l10n(data["dictionaries/month"]["dictionary"]["months"][d.month-1], "name", "h", lang))
        if ad:
            r.append(f"{d.year}\xa0ap.\xa0J.‑C.")
        r.append(f" {d.year}")
    elif lang.l == "es":
        r.append(f"{d.day}\xa0de\xa0")
        r.append(get_var_l10n(data["dictionaries/month"]["dictionary"]
                              ["months"][d.month-1], "name", "h", lang))
        r.append(" de ")
        if ad:
            r.append(f'{d.year}\xa0d.\xa0C.')
        r.append(f"{d.year}")
    elif lang.l in ("ja", "ko", "zh"):
        r.append(f'{d.year}{msg_l10n(lang=lang, string="say_date_cjk_year")}')
        r.append(f'{d.month}{msg_l10n(lang=lang, string="say_date_cjk_month")}')
        r.append(f'{d.day}{msg_l10n(lang=lang, string="say_date_cjk_day")}')

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
        return f'{to_sentence_case(get_var_l10n(data["dictionaries/language"]["dictionary"][lang.l], "name", format, lang), lang)} ({get_var_l10n(data["dictionaries/region"]["dictionary"][f"{lang.t}".lower()], "name", format, lang)})'


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

for dictionary in ["copyright_license", "disclaimer", "language", "month",
                   "region", "script", "share_link", "string", "validate_link",
                   "weekday"]:
    data[f"dictionaries/{dictionary}"] = {}
    data[f"dictionaries/{dictionary}"]["id"] = f"dictionaries/{dictionary}"
    data[f"dictionaries/{dictionary}"]["type"] = "dictionary"
    data[f"dictionaries/{dictionary}"]["dictionary_name"] = dictionary
    with open(Path(DICTS)/f"{dictionary}.json", "r", encoding="utf-8") as f:
        data[f"dictionaries/{dictionary}"]["dictionary"] = json.load(f)

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
                    F.append(data["dictionaries/copyright_license"]["dictionary"][license]["spdx"])
                    if spdx_license_num < spdx_license_count:
                        F.append(" OR ")
                        spdx_license_num += 1
                F.append(" -->\n")

            lang_dir: str
            if lang.s:
                lang_dir = data["dictionaries/script"]["dictionary"][lang.s]["dir"]
            elif data["dictionaries/language"]["dictionary"][lang.l].get("script"):
                lang_dir = data["dictionaries/script"]["dictionary"][data["dictionaries/language"]["dictionary"][lang.l]["script"]]["dir"]
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

                f'<link rel="external license" href{attribute_string(get_var_l10n(data["dictionaries/copyright_license"]["dictionary"][data[i_id]["copyright"]["license"][0]], "url", "i", lang))}>'

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

                f'<h1>{msg_l10n(get_var_l10n(data[i_id], "title", "h", lang), lang=lang, string="page_title_html")}</h1>'

                "<nav class=nav_buttons>"

                f'{make_nav_button("f", lang)}'
                f'{make_nav_button("p", lang)}'
                f'{make_nav_button("n", lang)}'
                f'{make_nav_button("l", lang)}'

                "</nav>"
            )

            if Path(INDEX/i_id/f"{lang}".lower()/"video.webm").is_file():
                F.append(
                    "<video controls poster=image.png preload=auto>"
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
                F.append("<p>")
                F.append(msg_l10n(lang, get_var_l10n(data[data[i_id]["location"]["series"]], "title", "t", lang), get_var_l10n(data[i_id], "title", "t", lang), get_var_l10n(data[i_id], "title", "t", lang), lang=lang, string="video_not_supported"))
                F.append("</p></video>")
            elif Path(INDEX/i_id/f"{lang}".lower()/"image.png").is_file():
                F.append("<picture")
                if get_var_l10n(data[i_id], "tooltip", "h", lang) is not None:
                    F.append(f' title{attribute_string(get_var_l10n(data[i_id], "tooltip", "t", lang))}')
                F.append(">")
                F.append(f'<img src=image.png fetchpriority=high alt{attribute_string(msg_l10n(lang=lang, string="see_transcript"))}>')
                F.append("</picture>")

                F.append("<nav class=nav_buttons>")

            F.append(
                f'{make_nav_button("f", lang)}'
                f'{make_nav_button("p", lang)}'
                f'{make_nav_button("n", lang)}'
                f'{make_nav_button("l", lang)}'

                "</nav><nav><details><summary>"
            )

            # TODO: Support multiple container depths

            F.append(msg_l10n(get_var_l10n(data[data[i_id]["location"]["series"]], "title", "h", lang), lang=lang, string="series_title_html"))
            F.append(msg_l10n(data[i_id]["location"]["page"], lang=lang, string="comma_page"))
            F.append(msg_l10n(get_var_l10n(data[i_id], "title", "h", lang), lang=lang, string="page_title_html"))
            F.append("</summary></details></nav>")

            # TODO: Page list

            F.append("<details>")
            F.append(f'<summary><h2>{msg_l10n(lang=lang, string="transcript_name")}</h2></summary>')
            F.append("<table>")

            for line in data[i_id]["transcript"]:
                # TODO: Check encyclopedia item type
                #line_h_type=data[f'encyclopedia/{line["h"]}']["type"]
                F.append("<tr>")
                F.append("<th scope=row>")
                line_h_label: str
                if data[f'encyclopedia/{line["h"]}'].get("name", {}).get("label"):
                    line_h_label = get_var_l10n(data[f'encyclopedia/{line["h"]}'].get("name", {}), "label", "h", lang)
                else:
                    line_h_label = get_var_l10n(data[f'encyclopedia/{line["h"]}'].get("name", {}), "label", "h", lang)
                F.append(line_h_label)

                F.append("<td>")
                if get_var_l10n(line, "d", "t", lang) == get_var_l10n(line, "d", "h", lang):
                    F.append("<p>")
                    F.append(get_var_l10n(line, "d", "h", lang))
                else:
                    F.append(get_var_l10n(line, "d", "h", lang))
            F.append("</table></details><hr>")

            F.append(f'<h2>{msg_l10n(lang=lang, string="log")}</h2>')

            for entry in data[i_id]["log"]:
                F.append(f'<article id=log_{print_date(date.fromisoformat(entry["date"]))}><details>')
                F.append(f'<summary><h3>{say_date(date.fromisoformat(entry["date"]), lang)}</h3></summary>')
                for line in entry["content"]:
                    if text_to_html(get_var_l10n(line, "p", "t", lang)) == get_var_l10n(line, "p", "h", lang):
                        F.append("<p>")
                    F.append(get_var_l10n(line, "p", "h", lang))
                F.append("</details></article>")

            F.append("<hr>")
            F.append("<p id=canonical_url>")
            F.append(msg_l10n(canonical, lang=lang, string="canonical_url"))
            F.append(f"<a href={canonical} hreflang={lang} type=text/html>")
            F.append(canonical)
            F.append("</a>")

            F.append("<details id=share_links>")
            F.append(f'<summary>{msg_l10n(lang=lang, string="share_this_page")}</summary>')
            F.append("<ul></ul></details>")

            F.append("<details id=validate_links>")
            F.append(f'<summary>{msg_l10n(lang=lang, string="validate_this_page")}</summary>')
            F.append("<ul></ul></details>")

            F.append("<footer><p><span class=nw>")
            F.append(msg_l10n(lang=lang, string="copyright_notice"))
            F.append(f'{data[i_id]["copyright"]["year"]["first"]}')
            if data[i_id]["copyright"]["year"].get("last"):
                F.append(msg_l10n(lang=lang, 
                                  string="copyright_year_separator"))
                F.append(f'{data[i_id]["copyright"]["year"]["last"]}')
            F.append("</span> ")
            F.append("<span translate=no>gabl.ink</span>")

            F.append(f'<p>{msg_l10n(lang=lang, string="license")}')
            F.append('<a rel="external license" href')
            F.append(attribute_string(get_var_l10n(data["dictionaries/copyright_license"]["dictionary"][data[i_id]["copyright"]["license"][0]], "url", "i", lang)))
            F.append(">")
            F.append(get_var_l10n(data["dictionaries/copyright_license"]["dictionary"][data[i_id]["copyright"]["license"][0]], "title", "h", lang))
            if data["dictionaries/copyright_license"]["dictionary"][data[i_id]["copyright"]["license"][0]].get("abbr"):
                F.append(msg_l10n(get_var_l10n(data["dictionaries/copyright_license"]["dictionary"][data[i_id]["copyright"]["license"][0]], "abbr", "h", lang), lang=lang, string="copyright_license_abbr"))
            F.append("</a>")

            if data[i_id].get("disclaimer"):
                F.append("<p>")
                if len(data[i_id]["disclaimer"]) == 1:
                    F.append(msg_l10n(lang=lang, string="disclaimer"))
                    F.append(get_var_l10n(data["dictionaries/disclaimer"]
                                          ["dictionary"][data[i_id]["disclaimer"][0]], "text", "h", lang))
                else:
                    F.append(msg_l10n(lang=lang, string="disclaimer_plural"))
                    F.append("<ul class=horizontal_list>")
                    for d in data[i_id]["disclaimer"]:
                        F.append("<li><p>")
                        F.append(get_var_l10n(data["dictionaries/disclaimer"]
                                              ["dictionary"][d], "text", "h", lang))
                    F.append("</ul>")

            F.append("</footer>")

            F.append("\n")

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

#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Gabel, the static site generator for gabl.ink."""

# Copyright © 2024–2026 gabl.ink

import json
import re
import sys
from pathlib import Path
from typing import Literal

__author__ = "gabl.ink"
__version__ = "0"


class Date:
    """Replacement for ``datetime.date`` and ``datetime.datetime``.
    
    Supports arbitrary positive or negative years. ``datetime`` only
    supports 1–9999.

    Works perfectly! If the input is already well-formed.
    """
    def __init__(
        self, y: int | None = None,
              m: int | None = None,
              d: int | None = None,
              h: int | None = None,
              n: int | None = None,
              s: int | None = None,
              f: int | None = None,
              z: int | None = None
    ):
        if (m is not None) and (m < 1 or m > 12):
            raise ValueError("Invalid month")
        elif (d is not None) and (d < 1 or d > 31):
            raise ValueError("Invalid day")
        elif (h is not None) and (h < 0 or h > 23):
            raise ValueError("Invalid hour")
        elif (n is not None) and (n < 0 or m > 59):
            raise ValueError("Invalid minute")
        elif (s is not None) and (s < 0 or s > 60):
            raise ValueError("Invalid second")
        elif (f is not None) and (f < 0 or f > 999):
            raise ValueError("Invalid fractional second")
        elif (z is not None) and (z < -720 or z > 840):
            raise ValueError("Invalid time offset")
        
        self.y: int | None = y
        self.m: int | None = m
        self.d: int | None = d
        self.h: int | None = h
        self.n: int | None = n
        self.s: int | None = s
        self.f: int | None = f
        self.z: int | None = z


    @classmethod
    def make(
        cls, y: int | None = None,
             m: int | None = None,
             d: int | None = None,
             h: int | None = None,
             n: int | None = None,
             s: int | None = None,
             f: int | None = None,
             z: int | None = None
    ) -> "d":
        return cls(y, m, d, h, n, s, f, z)
    

    @staticmethod
    def get(dt: "dict[int] | Date") -> "Date":
        if isinstance(dt, Date):
            return dt
        elif not isinstance(dt, dict) or not dt:
            raise ValueError("Invalid datetime object")

        return Date.make(dt)

        #dtdata: dict = {}

        #dstr: str
        #tstr: str

        #if "T" in dt:
        #    dstr=dt.split("T")[0]
        #    tstr=dt.split("T")[1]
        #elif ":" not in dt:
        #    dstr=dt
        #elif ":" in dt:
        #    tstr=dt

        #if dstr:
        #    if dstr.startswith("-"):
        #        dtdata["y"] = -int(dt.split("-")[1])
        #    elif len(dt.split("-")[0]) >= 4:
        #        dtdata["y"] = int(dt.split("-")[0])
        #    else:
        #        raise ValueError("missing year")
        #    if len(dt.split("-")[1]) == 2:
        #        dtdata["m"] = int(dt.split("-")[1])
        #    if dtdata["m"] and len(dt.split("-")[2]) == 2:
        #        dtdata["d"] = int(dt.split("-")[2])

        #if 

        #if dstr:
        #    dtdata["y"] = int(dstr[:-6])
        #    dtdata["m"] = int(dstr[-5:-5+2])
        #    dtdata["d"] = int(dstr[-2:])

        #if tstr:
    

    def say(d: "Date", flang: Lang | None = None) -> str:
        """Returns word form of date in HTML format."""
        if flang is None:
            flang = lang

        r: list[str] = [f"<time datetime={d}>"]

        ad: bool

        if d.y > 0 and d.y < 1000:
            ad = True
        else:
            ad = False

        if flang.l == "en":
            if flang.t == "US":
                r.append(
                    f"{get_l(ddict["month"]["months"][d.m-1]["name"])}"
                    f"\xa0{d.d}, "
                )
            elif flang.t == "GB":
                r.append(
                    f"{d.d}\xa0"
                    f"{get_l(ddict["month"]["months"][d.m-1]["name"])}"
                    " "
                )
            if ad:
                r.append("AD\xa0")
            r.append(f"{d.y}")
        elif flang.l == "fr":
            if d.d == 1:
                r.append("1er")
            else:
                r.append(f"{d.d}")
            r.append(
                "\xa0"
                f"{get_l(ddict["month"]["months"][d.m-1]["name"])}"
            )
            if ad:
                r.append(f"{d.y}\xa0ap.\xa0J.‑C.")
            r.append(f" {d.y}")
        elif flang.l == "es":
            r.append(
                f"{d.d}\xa0de\xa0"
                f"{get_l(ddict["month"]["months"][d.m-1]["name"])}"
                " de "
            )
            if ad:
                r.append(f"{d.y}\xa0d.\xa0C.")
            r.append(f"{d.y}")
        elif flang.l in ("ja", "ko", "zh"):
            r.append(
                f"{d.y}{msg_l10n(flang=flang, string="say_date_cjk_year")}"
                f"{d.m}{msg_l10n(flang=flang, string="say_date_cjk_month")}"
                f"{d.d}{msg_l10n(flang=flang, string="say_date_cjk_day")}"
            )

        r.append("</time>")

        return "".join(r)

    
    def __str__(self) -> str:
            """Returns a string suitable for a ``datetime`` attribute
            in HTML."""
            if not isinstance(self.y, int) or not self.y:
                raise ValueError("Invalid datetime object")

            if self.y <= 0:
                return ""
    
            r: list[str] = [f"{self.y:04d}"]

            if self.m:
                r.append(f"-{self.m:02d}")
    
            if self.d:
                r.append(f"-{self.d:02d}")

            if self.h:
                r.append(f"T{self.h:02d}")

            if self.n:
                r.append(f":{self.n:02d}")

            if self.s:
                r.append(f":{self.s:02d}")

            if self.f:
                r.append(f".{self.f:03d}")

            if self.z and self.h and self.n and self.s:
                if self.z == 0:
                    r.append("Z")
                else:
                    z_symbol: str
                    if self.z < 0:
                        z_symbol = "-"
                    else:
                        z_symbol = "+"
                    z_hours: str = f"{(abs(self.z) // 60):02d}"
                    z_minutes: str = f"{((abs(self.z)) - (abs(int(z_hours)) * 60)):02d}"
                    r.append(f"{z_symbol}{z_hours}{z_minutes}")
    
            return "".join(r)


class Lang:
    """Simpler (worse) replacement for ``langcodes.Language``.

    Supports all subtags except for extensions (``t`` and ``u``).

    Like ``Date``, works perfectly if the input is already well-formed.
    """
    def __init__(
        self, l: str,
              s: str | None = None,
              t: str | None = None,
              v: list[str] | None = None,
              x: str | None = None
    ):
        if not re.fullmatch(r"^[a-z]{2,3}$", l):
            raise ValueError("Invalid language subtag")
        elif (s is not None) and not re.fullmatch(r"^[A-Z][a-z]{3}$", s):
            raise ValueError("Invalid script subtag")
        elif (t is not None) and not re.fullmatch(r"^[A-Z]{2}$|^[0-9]{3}$", t):
            raise ValueError("Invalid territory subtag")
        
        self.l: str = l
        self.s: str | None = s
        self.t: str | None = t
        self.v: list[str] | None = v
        self.x: str | None = x

    @classmethod
    def make(
        cls, l: str,
             s: str | None = None,
             t: str | None = None,
             v: list[str] | None = None,
             x: str | None = None
    ) -> "Lang":
        return cls(l, s, t, v, x)

    @staticmethod
    def get(tag: "str | Lang") -> "Lang":
        if isinstance(tag, Lang):
            return tag
        elif not isinstance(tag, str) or not tag:
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

        return Lang.make(**langdata)

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

    @staticmethod
    def say(to_say: "Lang", fformat: str | None = None, flang: "Lang | None" = None) -> str:
        """Returns a formatted language name and region."""
        if flang is None:
            flang = lang
        if fformat is None:
            fformat = format
        if flang.l in ("en", "fr"):
            return f"{to_sentence_case(get_l(ddict["lang"][to_say.l]["name"], fformat, flang), flang)} ({get_l(ddict["region"][f"{to_say.t}".lower()]["name"], fformat, flang)})"


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


def close(tag: str | None = None, fformat: Literal["H", "X"] | None = None):
    if fformat is None:
        fformat = format
    if tag is None:
        if fformat == "X":
            return "/>"
        elif fformat == "H":
            return ">"
        else:
            raise ValueError("format must be H or X")
    elif fformat == "X":
        return f"</{tag}>"
    elif fformat == "H":
        return ""
    else:
        raise ValueError("format must be H or X")


def expand_parts(parts: list[str | int]) -> list[int]:
    """Returns a list of integers from a ``parts`` list.

    >>> expand_parts([1, 2, 3])
    [1, 2, 3]
    >>> expand_parts(["1-3"])
    [1, 2, 3]
    >>> expand_parts([4, 7, "1-5"])
    [1, 2, 3, 4, 5, 7]
    """
    r: set[int] = set()

    for part in parts:
        if isinstance(part, int):
            r.add(part)
        else:
            start, end = map(int, part.split("-"))
            r.update(range(start, end + 1))

    return sorted(r)


def get_i(i_item_file: Path) -> str:
    with open(i_item_file, "r", encoding="utf-8") as f:
        item_obj = json.load(f)
        return item_obj["id"]


def get_l(key: dict, fformat: Literal["A", "H", "i", "L", "p", "T", "t", "X"] | None = None, flang: L | None = None) -> str:
    if fformat is None:
        fformat = format
    if flang is None:
        flang = lang

    formats: str = "AHiLpTtX"
    options: list[str] = [f"{flang}", flang.l, "mul", "zxx", "z"]

    if fformat not in formats:
        raise ValueError("Invalid format given")

    def find_equals(pointer: str) -> str:
        to_find: tuple = key[o][f"{pointer}e"].split("_")

        # TODO: catch invalid equals
        if to_find[0] and to_find[0] not in formats:
            raise ValueError("Equals does not contain a valid format")
        elif to_find[0] and not to_find[1]:
            return get_l(key, to_find[0], flang)
        elif to_find[1] and not to_find[0]:
            return get_l(key, fformat, to_find[1])
        else:
            return get_l(key, to_find[0], to_find[1])

    # ASCII

    # HTML5
    if fformat == "H":
        for o in options:
            if o == "z":
                return ""

            to_check: dict = key.get(o, {})

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
                return get_l(key, fformat, Lang.get(to_check["e"]))
    # identifier
    elif fformat == "i":
        for o in options:
            if o == "z":
                return ""

            to_check: dict = key.get(o, {})
            
            if "i" in to_check:
                return to_check["i"]
            elif "if" in to_check:
                return eval(f'f"{to_check["if"]}"')
            elif "ie" in to_check:
                return find_equals("i")
            elif "e" in to_check:
                return get_l(key, fformat, Lang.get(to_check["e"]))
    # LaTeX
    elif fformat == "L":
        for o in options:
            if o == "z":
                return ""
                    
            to_check: dict = key.get(o, {})

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
                return get_l(key, fformat, Lang.get(to_check["e"]))
    # print
    elif fformat == "p":
        for o in options:
            if o == "z":
                return ""
            
            to_check: dict = key.get(o, {})

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
                return get_l(key, fformat, Lang.get(to_check["e"]))
    # TeX

    # text
    elif fformat == "t":
        for o in options:
            if o == "z":
                return ""

            to_check: dict = key.get(o, {})

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
                return get_l(key, fformat, Lang.get(to_check["e"]))
    # XHTML5 (polyglot)
    elif fformat == "X":
        for o in options:
            if o == "z":
                return ""

            to_check: dict = key.get(o, {})

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
                return get_l(key, fformat, Lang.get(to_check["e"]))


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


def language_list_entry(l: Lang) -> str:
    r: list[str] = ["<li"]

    if l.t is not None:
        r.append(
            f''' style="list-style-type:'{to_regional_indicators(l.t)}\xa0'">'''
        )

    if f"{l}" == f"{lang}":
        r.append("<b>")
    else:
        r.append(f"<a lang={l} href=../{f"{l}".lower()}/ hreflang={l}>")

    r.append(Lang.say(l, None, l))

    if f"{l}" == f"{lang}":
        r.append("</b>")
    else:
        r.append("</a>")

    return "".join(r)


def make_nav_button(button: Literal["f", "p", "n", "l"], flang: None | Lang = None) -> str:
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
            r.append(attr(msg_l10n(get_l(data[f"{data[i]["location"]["series"]}/{data[data[i]["location"]["series"]][button_id]}"]["title"], "t"), flang=flang, string="nav_button_page_title")))
        elif button in ("p", "n"):
            r.append(attr(msg_l10n(get_l(data[f"{data[i]["location"]["series"]}/{data[i]["location"][button_id]}"]["title"], "t"), string="nav_button_page_title")))
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


def msg_l10n(*args, string: str, flang: Lang | None = None) -> str:
    if flang is None:
        flang = lang
    return get_l(ddict["string"][string], "p", flang).format(*args)


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


def to_sentence_case(string: str, flang: Lang | None = None) -> str:
    """Capitalizes the first character of a string as appropriate for
    the language.

    >>> to_sentence_case("toki pona", Lang.get("tok"))
    'toki pona'
    >>> to_sentence_case("français", Lang.get("fr"))
    'Français'
    """
    if flang is None:
        flang = lang

    if flang.l == "tok":
        return string
    else:
        return f"{string[:1].upper()}{string[1:]}"


#def validate_data()->None:
#    for key in data:
#        if not unicodedata.is_normalized("NFC",key):
#            raise SystemExit("Key name not normalized in NFC")
#    for value in data.values():
#        if isinstance(value,str):
#            if not unicodedata.is_normalized("NFC",value):
#                raise SystemExit("String not normalized in NFC")


SCRIPT: Path = Path(__file__).resolve()
GABEL: Path = SCRIPT.parent
DICTS: Path = Path(GABEL)/"dicts"
INDEX: Path = Path(GABEL)/".."/"i"

data: dict = {}

item_files: list[Path] = [
    path
    for path in Path(INDEX).rglob("data.json")
    if path.is_file()
]

ddict: dict = {}

for dictionary in ["disclaim", "format", "lang", "license", "month", "region",
                   "script", "share", "string", "validate", "weekday"]:
    with open(Path(DICTS)/f"{dictionary}.json", "r", encoding="utf-8") as f:
        ddict[dictionary] = json.load(f)

for item_file in item_files:
    with open(item_file, "r", encoding="utf-8") as f:
        obj = json.load(f)
        obj_id = obj.get("id")
        data[obj_id] = obj

if __name__ == "__main__":
    sys.stderr.write("Generating pages…")

    # TODO: Make this a function(s); these variables are global.
    for item_file in item_files:
        i: str = get_i(item_file)

        if data[i]["type"] != "comic_page":
            continue

        for lang in data[i]["langs"]:
            lang: Lang = Lang.get(lang)
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

                f"<meta charset=utf-8{close()}"
                f'<meta name=viewport content="width=device-width,initial-scale=1"{close()}'

                f"<title>{msg_l10n(get_l(data[i]["title"], "t"), string="html_title")}</title>"

                f"<meta name=description content{attr(get_l(data[i]["description"], "t"))}{close()}"

                f"<meta name=robots content=index,follow{close()}"

                f"<link rel=canonical href={canonical} hreflang={lang} type=text/html{close()}"

                # TODO: `if type != comic_page` (sh:349)

                f"<link rel=stylesheet href={styles}/mul.css hreflang=zxx{close()}"
                f"<link rel=stylesheet href={styles}/{lang.l}.css hreflang=zxx{close()}"
                f"<link rel=stylesheet href={styles}/comic_page.css hreflang=zxx{close()}"

                f'<link rel="external license" href{attr(get_l(ddict["license"][data[i]["copyright"]["license"][0]]["url"], "i"))}{close()}'

                # TODO: Prefetches (starting at sh:420)

                f"<meta property=og:type content=article{close()}"
                f"<meta property=og:title content{attr(get_l(data[i]["title"], "t"))}{close()}"
                f"<meta property=og:description content{attr(get_l(data[i]["description"], "t"))}{close()}"
                f"<meta property=og:site_name content=gabl.ink{close()}"
                f"<meta property=og:url content={canonical}{close()}"
                f"<meta property=og:image content={canonical}image.png{close()}"
                # TODO: video_exists (sh:322–332, sh:454)
                f"<meta property=og:locale content={lang.l}_{lang.t}{close()}"

                "<script type=application/ld+json>{"
                '"@context":"https://schema.org",'
                '"@type":"WebPage"'
                "}</script>"

                "<header>"
                "<a href=https://gabl.ink/ id=gabldotink_logo>gabl.ink</a>"

                "<ul id=L>"
            )
            for l in sorted(data[i]["langs"]):
                l: Lang = Lang.get(l)
                F.append(language_list_entry(l))
            F.append(
                "</ul></header>"

                f"<h1>{msg_l10n(get_l(data[i]["title"]), string="page_title_html")}</h1>"

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
                    f"<source src=video.webm type=video/webm{close()}"
                )
                if Path(INDEX/i/f"{lang}".lower()/"subs.vtt").is_file():
                    F.append(
                        f"<track default src=subs.vtt srclang={lang} kind=subtitles "
                        f"label{attr(Lang.say(lang, "t"))}{close()}"
                    )
                if Path(INDEX/i/f"{lang}".lower()/"cc.vtt").is_file():
                    F.append(
                        f"<track src=cc.vtt srclang={lang} kind=captions "
                        f"label{attr(f"{Lang.say(lang, "t")}{msg_l10n(string="cc")}")}{close()}"
                    )
                F.append(
                    "<p>"
                    f"{msg_l10n(lang, get_l(data[data[i]["location"]["series"]]["title"], "t"), get_l(data[i]["title"], "t"), get_l(data[i]["title"], "t"), string="video_not_supported")}"
                    "</p></video>"
                )
            elif Path(INDEX/i/f"{lang}".lower()/"image.png").is_file():
                F.append("<picture id=M")
                if get_l(data[i].get("tooltip", {})) is not None:
                    F.append(f" title{attr(get_l(data[i].get("tooltip", {}), "t"))}")
                F.append(
                    ">"
                    f"<img src=image.png fetchpriority=high alt{attr(msg_l10n(string="see_transcript"))}{close()}"
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
                f"{msg_l10n(get_l(data[data[i]["location"]["series"]]["title"]), string="series_title_html")}"
                f"{msg_l10n(data[i]["location"]["page"], string="comma_page")}"
                f"{msg_l10n(get_l(data[i]["title"]), string="page_title_html")}"
                "</summary>"

                f"<ol id{attr("P")}>"
            )

            list_page_self: str = f"{data[i]["location"]["page"]}"

            for list_page in expand_parts(data[data[i]["location"]["series"]]["parts"]):
                F.append("<li>")
                if not get_l(data[i]["title"]):
                    if data[i]["location"]["page"] == list_page:
                        F.append("<b>")
                    F.append(msg_l10n(string="no_title"))
                    if data[i]["location"]["page"] == list_page:
                        F.append("</b>")
                else:
                    if data[i]["location"]["page"] == list_page:
                        if lang.l == "en":
                            F.append("“<b><cite>")
                        elif lang.l == "fr":
                            F.append(f"<b><cite class{attr("i")}>")
                        F.append(get_l(data[f"{data[i]["location"]["series"]}/{list_page}"]["title"]))
                        if lang.l == "en":
                            F.append("</cite></b>”")
                        elif lang.l == "fr":
                            F.append("</cite></b>")
                    else:
                        if lang.l == "en":
                            F.append(
                                f"“<a href{attr(f"../../{data[i]["location"]["series"]}/{list_page}/{f"{lang}".lower()}/")} "
                                f"hreflang{attr(f"{lang}")} "
                                f"type{attr("text/html")}>"
                                f"<cite>{get_l(data[f"{data[i]["location"]["series"]}/{list_page}"]["title"])}</cite>"
                                "</a>”"
                            )
                        elif lang.l == "fr":
                            F.append(
                                f"“<a href{attr(f"../../{data[i]["location"]["series"]}/{list_page}/{f"{lang}".lower()}/")} "
                                f"hreflang{attr(f"{lang}")} "
                                f"type{attr("text/html")}>"
                                f"<cite class{attr("i")}>{get_l(data[f"{data[i]["location"]["series"]}/{list_page}"]["title"])}</cite>"
                                "</a>"
                            )
                F.append("</li>")

            F.append(
                "</ol></details></nav>"
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
                line_h_label: str = get_l(data[f"encyclopedia/{line["H"]}"].get("name", {}).get("label", {}))
                F.append(
                    f"{line_h_label}"
                    f"{close("th")}"
                    "<td>"
                )
                F.append(get_l(line["d"]))
                F.append(
                    f"{close("td")}"
                    f"{close("tr")}"
                )
            F.append(
                "</table></details><hr>"
                f"<h2>{msg_l10n(string="log")}</h2>"
            )

            for entry in data[i]["log"]:
                F.append(
                    f"<article id=log_{Date.make(**entry["date"])}><details>"
                    f"<summary><h3>{Date.say(Date.make(**entry["date"]))}</h3></summary>"
                )
                for line in entry["content"]:
                    if get_l(line.get("p")):
                        F.append(f"<p>{get_l(line["p"])}{close("p")}")
                    elif get_l(line.get("x")):
                        F.append(get_l(line["x"]))
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
                f"{attr(get_l(ddict["license"][data[i]["copyright"]["license"][0]]["url"], "i"))}"
                ">"
                f"{get_l(ddict["license"][data[i]["copyright"]["license"][0]]["title"])}"
            )
            if ddict["license"][data[i]["copyright"]["license"][0]].get("abbr"):
                F.append(msg_l10n(get_l(ddict["license"][data[i]["copyright"]["license"][0]]["abbr"]), string="copyright_license_abbr"))
            F.append("</a>")

            if data[i].get("disclaimer"):
                F.append("<p>")
                if len(data[i]["disclaimer"]) == 1:
                    F.append(
                        f"{msg_l10n(string="disclaimer")}"
                        f"{get_l(ddict["disclaim"][data[i]["disclaimer"][0]]["text"])}"
                    )
                else:
                    F.append(
                        f"{msg_l10n(string="disclaimer_plural")}"
                        "<ul class=horizontal_list>"
                    )
                    for d in data[i]["disclaimer"]:
                        F.append(
                            "<li><p>"
                            f"{get_l(ddict["disclaim"][d]["text"])}"
                        )
                    F.append("</ul>")

            F.append(
                "</footer>"
                f"{close("body")}"
                f"{close("html")}"
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

    sys.stderr.write(" done\n")

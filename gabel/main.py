#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0

# I’ve been meaning to learn Python anyway

import json
import re
import sys
from datetime import date
from pathlib import Path

# Arch: python-langcodes
from langcodes import Language

script:Path=Path(__file__).resolve()
gabel:Path=script.parent
dicts:Path=Path(gabel)/"dictionaries"
index:Path=Path(gabel)/".."/"i"
encyclopedia:Path=Path(index)/"encyclopedia"

data:dict={}

item_files:list=[
    path
    for path in Path(index).rglob("data.json")
    if path.is_file()
]

for dictionary in ["copyright_license","disclaimer","language","month","region","script","share_link","string","validate_link","weekday"]:
    data[f"dictionaries/{dictionary}"]={}
    data[f"dictionaries/{dictionary}"]["id"]=f"dictionaries/{dictionary}"
    data[f"dictionaries/{dictionary}"]["type"]="dictionary"
    data[f"dictionaries/{dictionary}"]["dictionary_name"]=dictionary
    with open(Path(dicts)/f"{dictionary}.json","r",encoding="utf-8") as f:
        data[f"dictionaries/{dictionary}"]["dictionary"]=json.load(f)
    user_dictionary=Path(index)/"dictionaries"/dictionary/"data.json"
    if user_dictionary.is_file():
        with open(user_dictionary,"r",encoding="utf-8") as f:
            data[f"dictionaries/{dictionary}"].update(json.load(f))

for i in item_files:
    with open(i,"r",encoding="utf-8") as f:
        obj=json.load(f)
        obj_id=obj.get("id")
        data[obj_id]=obj

def attribute_string(string:str)->str:
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
    # In HTML5, `attribute` is equivalent to `attribute=""`
    if not string:
        return ""

    quoted:bool

    if any(c in string for c in " \"'=<>`\n\r\t\v\f"):
        quoted=True
    else:
        quoted=False

    quote_char:str

    if quoted:
        if '"' in string and "'" not in string:
            quote_char="'"
        elif "'" in string and '"' not in string:
            quote_char='"'
        elif '"' in string and "'" in string:
            if string.count('"')>string.count("'"):
                quote_char="'"
            else:
                quote_char='"'
        else:
            quote_char='"'

    string=re.sub(r"&(?=[#A-Za-z])","&amp;",string) # &#38;

    if quoted:
        if quote_char=='"':
            string=string.replace('"',"&#34;") # &quot;
        elif quote_char=="'":
            string=string.replace("'","&#39;") # &apos;
        return f"={quote_char}{string}{quote_char}"
    else:
        return f"={string}"

def expand_parts(parts:list)->list:
    """Returns a list of integers from a `parts` list.

    >>> expand_parts([1,2,3])
    [1, 2, 3]
    >>> expand_parts(["1-3"])
    [1, 2, 3]
    >>> expand_parts([4, 7, "1-5"])
    [1, 2, 3, 4, 5, 7]
    """
    result=set()

    for part in parts:
        if isinstance(part,int):
            result.add(part)
        else:
            start,end=map(int,part.split("-"))
            result.update(range(start,end+1))

    return sorted(result)

def get_i_id(i:Path)->str:
    with open(i,"r",encoding="utf-8") as f:
        obj=json.load(f)
        return obj["id"]

def get_var_l10n(index,key:str|int,format:str,l10n_lang:Language)->str:
    # e.g. get_var_l10n(data["jrco_beta/1"]["location"],"series","text",lang)

    for o in str(l10n_lang),l10n_lang.language,"mul","zxx","e":
        if o=="e":
            return ""

        if format=="id":
            if "id" in index.get(key,{}).get(o,{}):
                return index[key][o]["id"]
            elif "equal" in index.get(key,{}).get(o,{}):
                return get_var_l10n(index,key,format,Language.get(index[key][o]["equal"]))

        if format=="print":
            if "print" in index.get(key,{}).get(o,{}):
                return index[key][o]["print"]
            elif "equal" in index.get(key,{}).get(o,{}):
                return get_var_l10n(index,key,format,Language.get(index[key][o]["equal"]))

        if format=="text":
            if "text" in index.get(key,{}).get(o,{}):
                return index[key][o]["text"]
            elif "equal" in index.get(key,{}).get(o,{}):
                return get_var_l10n(index,key,format,Language.get(index[key][o]["equal"]))

        if format=="html":
            if "html" in index.get(key,{}).get(o,{}):
                return index[key][o]["html"]
            elif "text" in index.get(key,{}).get(o,{}):
                return text_to_html(index[key][o]["text"])
            elif "equal" in index.get(key,{}).get(o,{}):
                return get_var_l10n(index,key,format,Language.get(index[key][o]["equal"]))

def id_base(i:str)->str:
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

def id_parent(i:str)->str|None:
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

# TODO: remove global variable (`data`) reference
def make_nav_button(button:str,lang:Language)->str:
    button_arrow,button_id,button_fl={
        "f":("⇦","first","first"),
        "p":("←","prev","first"),
        "n":("→","next","last"),
        "l":("⇨","last","last"),
    }[button]

    r:list=["<div class=nav_button title"]

    if data[i_id]["location"]["page"]==data[data[i_id]["location"]["series"]].get(button_fl):
        r.append(attribute_string(msg_l10n(msg_l10n(lang=lang,string=f"nav_button_{button_id}_inline"),lang=lang,string="this_is_x_page")))
        r.append(">")
    else:
        if button in ("f","l"):
            r.append(attribute_string(msg_l10n(get_var_l10n(data[f'{data[i_id]["location"]["series"]}/{data[data[i_id]["location"]["series"]][button_id]}'],"title","text",lang),lang=lang,string="nav_button_page_title")))
        elif button in ("p","n"):
            r.append(attribute_string(msg_l10n(get_var_l10n(data[f'{data[i_id]["location"]["series"]}/{data[i_id]["location"][button_id]}'],"title","text",lang),lang=lang,string="nav_button_page_title")))
        r.append(">")
        r.append("<a href=../../")
        if button in ("f","l"):
            r.append(str(data[data[i_id]["location"]["series"]][button_id]))
        elif button in ("p","n"):
            r.append(str(data[i_id]["location"][button_id]))
        r.append(f"/{str(lang).lower()}/ hreflang={lang}>")

    r.append(f'<span class=nav_button_arrow aria-hidden=true>{button_arrow}</span><br>{msg_l10n(lang=lang,string=f"nav_button_{button_id}")}')

    if data[i_id]["location"]["page"]!=data[data[i_id]["location"]["series"]].get(button_fl,{}):
        r.append("</a>")

    r.append("</div>")

    return "".join(r)

def make_share_link(name:str)->str:
    r:list=[f"<li id=share_link_{name}>"]
    r.append('<a href')

    query:dict={}
    for key in "title","url","text","hashtag":
        if data["dictionaries/share_link"][name].get(key,{}).get("key"):
            pass

    r.append(data["dictionaries/share_link"][name]["base"])

def msg_l10n(*args,lang:Language,string:str)->str:
    return get_var_l10n(data["dictionaries/string"]["dictionary"],string,"print",lang).format(*args)

def print_date(d:date)->str:
    """Returns a date string suitable for an HTML `datetime` attribute.

    >>> print_date(date.fromisoformat("20260407"))
    '2026-04-07'
    """
    return f"{d.year:04}-{d.month:02}-{d.day:02}"

def text_to_html(string:str)->str:
    string=re.sub(r"&(?=[#A-Za-z])","&amp;",string) # &#38;
    string=string.replace("<","&lt;") # &#60;
    string=string.replace("\u200b","<wbr>")
    string=string.replace("\n","<br>")
    return string

def to_regional_indicators(string:str)->str:
    """Returns a set of regional indicators from an uppercase string.

    >>> to_regional_indicators("US")
    '🇺🇸'
    """
    out_chars=[]
    for ch in string:
        out_chars.append(chr(0x1F1E6+(ord(ch)-ord("A"))))
    return "".join(out_chars)

def to_sentence_case(string:str,lang:Language)->str:
    """Capitalizes the first character of a string as appropriate for
    the language.

    >>> to_sentence_case("toki pona",Language.get("tok"))
    'toki pona'
    >>> to_sentence_case("français",Language.get("fr"))
    'Français'
    """
    if lang.language=="tok":
        return string
    else:
        return f"{string[:1].upper()}{string[1:]}"

# The shell script supports negative years, but `datetime` does not.
def say_date(d:date,lang:Language)->str:
    """Returns word form of date in HTML format.

    >>> say_date(date.fromisoformat("20220401"),Language.get("fr"))
    '<time datetime=2022-04-01>1er\xa0avril 2022</time>'
    """
    r:list=[f"<time datetime={print_date(d)}>"]

    ad:bool

    if d.year>0 and d.year<1000:
        ad=True
    else:
        ad=False

    if lang.language=="en":
        if lang.region=="US":
            r.append(get_var_l10n(data["dictionaries/month"]["dictionary"]["months"][d.month-1],"name","html",lang))
            r.append(f"\xa0{d.day}, ")
        elif lang.region=="GB":
            r.append(f"{d.day}\xa0")
            r.append(get_var_l10n(data["dictionaries/month"]["dictionary"]["months"][d.month-1],"name","html",lang))
            r.append(" ")
        if ad:
            r.append('<abbr title="anno Domini">AD</abbr>\xa0')
        r.append(str(d.year))
    elif lang.language=="fr":
        if d.day==1:
            r.append("1er")
        else:
            r.append(str(d.day))
        r.append("\xa0")
        r.append(get_var_l10n(data["dictionaries/month"]["dictionary"]["months"][d.month-1],"name","html",lang))
        if ad:
            r.append(f'{d.year}\xa0<abbr title="après Jésus‐Christ">ap.\xa0J.‑C.</abbr>')
        r.append(f" {d.year}")
    elif lang.language=="es":
        r.append(f"{d.day}\xa0de\xa0")
        r.append(get_var_l10n(data["dictionaries/month"]["dictionary"]["months"][d.month-1],"name","html",lang))
        r.append(" de ")
        if ad:
            r.append(f'{d.year}\xa0<abbr title="después de Cristo">d.\xa0C.</abbr>')
        r.append(str(d.year))
    elif lang.language in ("ja","ko","zh"):
        r.append(f'{d.year}{msg_l10n(lang=lang,string="say_date_cjk_year")}')
        r.append(f'{d.month}{msg_l10n(lang=lang,string="say_date_cjk_month")}')
        r.append(f'{d.day}{msg_l10n(lang=lang,string="say_date_cjk_day")}')

    r.append("</time>")

    return "".join(r)

def say_lang(lang:Language,format:str)->str:
    """Returns a formatted language name and region.

    >>> say_lang(Language.get("en-US"),"text")
    'English (United States)'
    >>> say_lang(Language.get("fr-FR"),"text")
    'Français (France)'
    """
    if lang.language in ("en","fr"):
        return f'{to_sentence_case(get_var_l10n(data["dictionaries/language"]["dictionary"][lang.language],"name",format,lang),lang)} ({get_var_l10n(data["dictionaries/region"]["dictionary"][str(lang.region).lower()],"name",format,lang)})'

if __name__=="__main__":
    sys.stderr.write("section start: items\n")

    for i in item_files:
        i_id:str=get_i_id(i)

        if data[i_id]["type"]!="comic_page":
            continue

        for lang in data[i_id]["langs"]:
            lang=Language.get(lang)

            canonical:str=f'https://gabl.ink/i/{data[i_id]["id"]}/{str(lang).lower()}/'

            F:list=["<!DOCTYPE html>\n"]

            F.append(f'<!-- SPDX-License-Identifier: {data["dictionaries/copyright_license"]["dictionary"][data[i_id]["copyright"]["license"][0]]["spdx"]} -->\n')

            # TODO: Skipping the dir attribute for now, but it should be implemented later (sh:338)
            F.append(f"<html lang={lang}>")

            F.append('<meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">')

            F.append(f'<title>{msg_l10n(get_var_l10n(data[i_id],"title","text",lang),lang=lang,string="html_title")}</title>')

            F.append(f'<meta name=description content{attribute_string(get_var_l10n(data[i_id],"description","text",lang))}>')

            F.append("<meta name=robots content=index,follow>")

            F.append(f"<link rel=canonical href={canonical} hreflang={lang} type=text/html>")

            # TODO: Only works for one type of depth, but I want to redesign that whole system anyway (sh:349–385)
            styles:str="../../../../gabel/styles"

            # TODO: `if type != comic_page` (sh:349)

            F.append(f"<link rel=stylesheet href={styles}/{lang.language}.css hreflang=zxx type=text/css>")
            F.append(f"<link rel=stylesheet href={styles}/comic_page.css hreflang=zxx type=text/css>")

            F.append(f'<link rel="external license" href{attribute_string(get_var_l10n(data["dictionaries/copyright_license"]["dictionary"][data[i_id]["copyright"]["license"][0]],"url","id",lang))}>')

            # TODO: Prefetches (starting at sh:420)

            F.append("<meta property=og:type content=article>")
            F.append(f'<meta property=og:title content{attribute_string(get_var_l10n(data[i_id],"title","text",lang))}>')
            F.append(f'<meta property=og:description content{attribute_string(get_var_l10n(data[i_id],"description","text",lang))}>')
            F.append("<meta property=og:site_name content=gabl.ink>")
            F.append(f"<meta property=og:url content={canonical}>")
            F.append(f"<meta property=og:image content={canonical}image.png>")
            # TODO: video_exists (sh:322–332, sh:454)
            F.append(f"<meta property=og:locale content={lang.language}_{lang.territory}>")

            F.append("<header>")
            F.append("<a href=https://gabl.ink/ id=gabldotink_logo>gabl.ink</a>")

            F.append("<ul id=lang_select>")
            for l in sorted(data[i_id]["langs"]):
                l=Language.get(l)

                F.append(f"<li data-lang_select_flag={to_regional_indicators(l.region)}>")

                if l==lang:
                    F.append("<b>")
                else:
                    F.append(f"<a lang={l} href=../{str(l).lower()}/ hreflang={l}>")

                F.append(say_lang(l,"html"))

                if l==lang:
                    F.append("</b>")
                else:
                    F.append("</a>")
            F.append("</ul></header>")

            F.append(f'<h1>{msg_l10n(get_var_l10n(data[i_id],"title","html",lang),lang=lang,string="page_title_html")}</h1>')

            F.append("<nav class=nav_buttons>")

            F.append(make_nav_button("f",lang))
            F.append(make_nav_button("p",lang))
            F.append(make_nav_button("n",lang))
            F.append(make_nav_button("l",lang))

            F.append("</nav>")

            if Path(index/i_id/str(lang).lower()/"video.webm").is_file():
                F.append("<video controls poster=image.png preload=auto>")
                F.append("<source src=video.webm type=video/webm>")
                if Path(index/i_id/str(lang).lower()/"subs.vtt").is_file():
                    F.append(f"<track default src=subs.vtt srclang={lang} kind=subtitles ")
                    F.append(f'label{attribute_string(say_lang(lang,"text"))}>')
                if Path(index/i_id/str(lang).lower()/"cc.vtt").is_file():
                    F.append(f"<track src=cc.vtt srclang={lang} kind=captions ")
                    F.append(f'''label{attribute_string(f'{say_lang(lang,"text")}{msg_l10n(lang=lang,string="cc")}')}>''')
                F.append("<p>")
                F.append(msg_l10n(lang,get_var_l10n(data[data[i_id]["location"]["series"]],"title","text",lang),get_var_l10n(data[i_id],"title","text",lang),get_var_l10n(data[i_id],"title","text",lang),lang=lang,string="video_not_supported"))
                F.append("</p></video>")
            elif Path(index/i_id/str(lang).lower()/"image.png").is_file():
                F.append("<picture")
                if get_var_l10n(data[i_id],"tooltip","html",lang) is not None:
                    F.append(f' title{attribute_string(get_var_l10n(data[i_id],"tooltip","text",lang))}')
                F.append(">")
                F.append(f'<img src=image.png fetchpriority=high alt{attribute_string(msg_l10n(lang=lang,string="see_transcript"))}>')
                F.append("</picture>")

                F.append("<nav class=nav_buttons>")

            F.append(make_nav_button("f",lang))
            F.append(make_nav_button("p",lang))
            F.append(make_nav_button("n",lang))
            F.append(make_nav_button("l",lang))

            F.append("</nav><nav><details><summary>")

            # TODO: Support multiple container depths

            F.append(msg_l10n(get_var_l10n(data[data[i_id]["location"]["series"]],"title","html",lang),lang=lang,string="series_title_html"))
            F.append(msg_l10n(data[i_id]["location"]["page"],lang=lang,string="comma_page"))
            F.append(msg_l10n(get_var_l10n(data[i_id],"title","html",lang),lang=lang,string="page_title_html"))
            F.append("</summary></details></nav>")

            # TODO: Page list

            F.append("<details>")
            F.append(f'<summary><h2>{msg_l10n(lang=lang,string="transcript_name")}</h2></summary>')
            F.append("<table>")

            for line in data[i_id]["transcript"]:
                # TODO: Check encyclopedia item type
                #line_h_type=data[f'encyclopedia/{line["h"]}']["type"]
                F.append("<tr>")
                F.append("<th scope=row>")
                line_h_label:str
                if data[f'encyclopedia/{line["h"]}'].get("name",{}).get("label"):
                    line_h_label=get_var_l10n(data[f'encyclopedia/{line["h"]}'].get("name",{}),"label","html",lang)
                else:
                    line_h_label=get_var_l10n(data[f'encyclopedia/{line["h"]}'].get("name",{}),"label","html",lang)
                F.append(line_h_label)

                F.append("<td>")
                if get_var_l10n(line,"d","text",lang)==get_var_l10n(line,"d","html",lang):
                    F.append("<p>")
                    F.append(get_var_l10n(line,"d","html",lang))
                else:
                    F.append(get_var_l10n(line,"d","html",lang))
            F.append("</table></details><hr>")

            F.append(f'<h2>{msg_l10n(lang=lang,string="log")}</h2>')

            for entry in data[i_id]["log"]:
                F.append(f'<article id=log_{print_date(date.fromisoformat(entry["date"]))}><details>')
                F.append(f'<summary><h3>{say_date(date.fromisoformat(entry["date"]),lang)}</h3></summary>')
                for line in entry["content"]:
                    if text_to_html(get_var_l10n(line,"p","text",lang))==get_var_l10n(line,"p","html",lang):
                        F.append("<p>")
                        F.append(get_var_l10n(line,"p","html",lang))
                    else:
                        F.append(get_var_l10n(line,"p","html",lang))
                F.append("</details></article>")

            F.append("<hr>")
            F.append("<p id=canonical_url>")
            F.append(msg_l10n(canonical,lang=lang,string="canonical_url"))
            F.append(f"<a href={canonical} hreflang={lang} type=text/html>")
            F.append(canonical)
            F.append("</a>")

            F.append("<details id=share_links>")
            F.append(f'<summary>{msg_l10n(lang=lang,string="share_this_page")}</summary>')
            F.append("<ul></ul></details>")

            F.append("<details id=validate_links>")
            F.append(f'<summary>{msg_l10n(lang=lang,string="validate_this_page")}</summary>')
            F.append("<ul></ul></details>")

            F.append("<footer><p><span class=nw>")
            F.append(msg_l10n(lang=lang,string="copyright_notice"))
            F.append(str(data[i_id]["copyright"]["year"]["first"]))
            if data[i_id]["copyright"]["year"].get("last"):
                F.append(msg_l10n(lang=lang,string="copyright_year_separator"))
                F.append(str(data[i_id]["copyright"]["year"]["last"]))
            F.append("</span>")
            F.append("<span translate=no>gabl.ink</span>")

            F.append(f'<p>{msg_l10n(lang=lang,string="license")}')
            F.append('<a rel="external license" href')
            F.append(attribute_string(get_var_l10n(data["dictionaries/copyright_license"]["dictionary"][data[i_id]["copyright"]["license"][0]],"url","id",lang)))
            F.append(">")
            F.append(get_var_l10n(data["dictionaries/copyright_license"]["dictionary"][data[i_id]["copyright"]["license"][0]],"title","html",lang))
            if data["dictionaries/copyright_license"]["dictionary"][data[i_id]["copyright"]["license"][0]].get("abbr"):
                F.append(msg_l10n(get_var_l10n(data["dictionaries/copyright_license"]["dictionary"][data[i_id]["copyright"]["license"][0]],"abbr","html",lang),lang=lang,string="copyright_license_abbr"))
            F.append("</a>")

            if data[i_id].get("disclaimer"):
                if len(data[i_id].get("disclaimer"))==1:
                    F.append("<p>")
                    F.append(msg_l10n(lang=lang,string="disclaimer"))
                    F.append(get_var_l10n(data["dictionaries/disclaimer"]["dictionary"][data[i_id]["disclaimer"][0]],"text","html",lang))
                else:
                    F.append("<p>")
                    F.append(msg_l10n(lang=lang,string="disclaimer_plural"))
                    F.append("<ul class=horizontal_list>")
                    for d in data[i_id]["disclaimer"]["dictionary"]:
                        F.append("<li><p>")
                        F.append(get_var_l10n(d,"text","html",lang))
                    F.append("</ul>")

            F.append("</footer>")

            output_file=Path(index)/i_id/str(lang).lower()/"index.html"
            output_file.parent.mkdir(parents=True,exist_ok=True)
            output_file.touch(exist_ok=True)

            output="".join(F)
            
            with open(output_file,"r+",encoding="utf-8",newline="") as output_file:
                # Only write if there is a change
                if output!=output_file.read():
                    output_file.seek(0)
                    output_file.truncate()
                    output_file.write(output)

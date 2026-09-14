#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0

# I’ve been meaning to learn Python anyway

import json
import os
import sys
from datetime import date
from pathlib import Path

from interlang import get_var_l10n,print_date,say_date
from text_to_htm import text_to_html,attribute_string
#from id_split import id_parent,id_base

# Arch: python-langcodes
from langcodes import Language

def get_i_id(i:Path)->str:
    with open(i,"r",encoding="utf-8") as f:
        obj=json.load(f)
        return obj["id"]

def to_sentence_case(string:str,lang:Language)->str:
    if lang.language=="tok":
        return string
    else:
        return f"{string[:1].upper()}{string[1:]}"

def to_regional_indicators(string:str)->str:
    out_chars=[]
    for ch in string:
        out_chars.append(chr(0x1F1E6+(ord(ch)-ord("A"))))
    return ''.join(out_chars)

def say_lang(lang:Language,format:str)->str:
    if lang.language in ("en","fr"):
        return f'{to_sentence_case(get_var_l10n(data["dictionaries/language"]["dictionary"][lang.language],"name",format,lang),lang)} ({get_var_l10n(data["dictionaries/region"]["dictionary"][str(lang.region).lower()],"name",format,lang)})'

def msg_l10n(*args,lang:Language,string:str)->str:
    return get_var_l10n(data["dictionaries/string"]["dictionary"],string,"print",lang).format(*args)

# TODO: remove global variable (`data`) reference
def make_nav_button(button:str,lang:Language)->str:
    button_arrow,button_id,button_fl={
        "f":("⇦","first","first"),
        "p":("←","prev","first"),
        "n":("→","next","last"),
        "l":("⇨","last","last"),
    }[button]

    r:list=["<div class=nav_button title"]

    if data[i_id]["location"]["page"]==data[data[i_id]["location"]["series"]].get(button_fl,{}):
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

    return ''.join(r)

def expand_parts(parts:list)->list:
    result=set()

    for part in parts:
        if isinstance(part,int):
            result.add(part)
        else:
            start,end=map(int,part.split("-"))
            result.update(range(start,end+1))

    return sorted(result)

if __name__=="__main__":
    script:Path=Path(os.path.abspath(sys.argv[0]))
    scripts:Path=Path(os.path.dirname(script))
    gabel:Path=Path(scripts)/".."
    lib:Path=Path(scripts)/"lib"
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

    for i in item_files:
        with open(i,"r",encoding="utf-8") as f:
            obj=json.load(f)
            obj_id=obj.get("id")
            data[obj_id]=obj

    sys.stderr.write("section start: items\n")

    for i in item_files:
        i_id:str=get_i_id(i)

        if data[i_id]["type"]!="comic_page":
            continue

        for lang in data[i_id]["langs"]:
            lang:Language=Language.get(lang)

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

            F.append(f"<link rel=preload href={styles}/{lang.language}.css as=style hreflang=zxx type=text/css>")
            F.append(f"<link rel=preload href={styles}/comic_page.css as=style hreflang=zxx type=text/css>")
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
                l:Language=Language.get(l)

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
                F.append(f'<summary><h3>{say_date(date.fromisoformat(entry["date"]),lang,data)}</h3></summary>')
                for line in entry["content"]:
                    if text_to_html(get_var_l10n(line,"p","text",lang))==get_var_l10n(line,"p","html",lang):
                        F.append("<p>")
                        F.append(get_var_l10n(line,"p","html",lang))
                    else:
                        F.append(get_var_l10n(line,"p","html",lang))
                    

            with open(Path(index)/i_id/str(lang).lower()/"index_py.html","w+",encoding="utf-8",newline='') as output_file:
                # Only write if there is a change
                if F!=output_file.read():
                    output_file.write(''.join(F))

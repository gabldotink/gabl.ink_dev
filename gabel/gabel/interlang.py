# SPDX-License-Identifier: CC0-1.0

from datetime import date

from text_to_htm import text_to_html

from langcodes import Language

def get_var_l10n(index,key:str|int,format:str,l10n_lang:Language)->str:
    # e.g. get_var_l10n(data["jrco_beta/1"]["location"],"series","text",lang)

    for o in str(l10n_lang),l10n_lang.language,"mul","zxx","e":
        if o=="e":
            return ''

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

# The shell script supports negative years, but `datetime` does not.
def say_date(d:date,lang:Language,data:dict)->str:
    r:list=[f"<time datetime={d.year:04}-{d.month:02}-{d.day:02}>"]

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
            r.append(f'{d.year}\xa0<abbr title="après Jésus‐Christ">ap.\xa0J.‐C.</abbr>')
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

    return ''.join(r)

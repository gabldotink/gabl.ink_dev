# SPDX-License-Identifier: CC0-1.0

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

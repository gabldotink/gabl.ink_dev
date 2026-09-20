# SPDX-License-Identifier: CC0-1.0

import re

def text_to_html(string:str)->str:
    string:str=re.sub(r"&(?=[#A-Za-z])","&amp;",string) # &#38;
    string:str=string.replace("<","&lt;") # &#60;
    string:str=string.replace("\n","<br>")
    return string

# This function assumes the input is plaintext!
def attribute_string(string:str)->str:
    # In HTML5, `attribute` is equivalent to `attribute=""`
    if not string:
        return ''

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

    string:str=re.sub(r"&(?=[#A-Za-z])","&amp;",string) # &#38;

    if quoted:
        if quote_char=='"':
            string:str=string.replace('"',"&#34;") # &quot;
        elif quote_char=="'":
            string:str=string.replace("'","&#39;") # &apos;
        return f"={quote_char}{string}{quote_char}"
    else:
        return f"={string}"

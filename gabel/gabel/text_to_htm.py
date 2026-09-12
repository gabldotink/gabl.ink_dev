# SPDX-License-Identifier: CC0-1.0

import re

def text_to_html(string:str)->str:
    string:str=re.sub(r"&(?=[#A-Za-z])","&amp;",string) # &#38;
    string:str=string.replace("<","&lt;") # &#60;
    string:str=string.replace("\n","<br>")
    return string

# SPDX-License-Identifier: CC0-1.0

def make_share_link(name:str,data:dict)->str:
    r:dict=[f"<li id=share_link_{name}>"]
    r.append('<a href')

    query:dict={}
    for key in ["title","url","text","hashtag"]:
        if data["dictionaries/share_link"][name].get(key,{}).get("key"):
            pass

    r.append(data["dictionaries/share_link"][name]["base"])

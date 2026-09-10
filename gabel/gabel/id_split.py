# SPDX-License-Identifier: CC0-1.0

"""From `foo/bar/baz`, get `foo/bar`"""
def id_parent(i_id:str)->str:
    if "/" in i_id:
        return i_id.rpartition("/")[0]
    else:
        return None

"""From `foo/bar/baz`, get `baz`"""
def id_base(i_id:str)->str:
    if "/" in i_id:
        return i_id.rpartition("/")[2]
    else:
        return i_id

# SPDX-License-Identifier: CC0-1.0

import cython

@cython.locals(quoted=cython.bint,quote_char=cython.str)
cdef str attribute_string(str string)

@cython.locals(result=cython.set)
cdef list expand_parts(list parts)

cdef str get_i_id(i)

@cython.locals(o=cython.str)
cdef str get_var_l10n(dict index,str key,str format,l10n_lang)

cdef str id_base(str i)

cdef id_parent(str i)

@cython.locals(button_arrow=cython.str,button_id=cython.str,button_fl=cython.str,r=cython.list)
cdef str make_nav_button(str button,lang)

# Function not done
#@cython.locals(r=cython.list,query=python.dict)
#cdef str make_share_link(str name)

# Doesn’t compile
#cdef str msg_l10n(args=*,lang,str string)

cdef str print_date(d)

cdef str text_to_html(str string)

@cython.locals(out_chars=cython.list,ch=cython.str)
cdef str to_regional_indicators(str string)

cdef str to_sentence_case(str string,lang)

@cython.locals(r=cython.list,ad=cython.bint)
cdef str say_date(date,lang)

cdef str say_lang(lang,str format)

cdef dict data

cdef list item_files

cdef str dictionary

cdef dict obj
cdef str obj_id

cdef str i_id

cdef str canonical

cdef list F

cdef int spdx_license_count
cdef int spdx_license_num
cdef str L

cdef str styles

cdef str line_h_label

cdef dict entry
cdef dict line

cdef str output

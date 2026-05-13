lang = []
def next():
    if lang:
        return f'[bruhlang] {lang.pop(0)}'
    else:
        return ''
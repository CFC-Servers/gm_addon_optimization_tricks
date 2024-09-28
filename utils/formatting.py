def format_size(size):
    if size < 1000:
        return f"{size} B"

    if size < 1000000:
        kbs = size / 1000
        rounded = round(kbs, 2)
        return f"{rounded} KB"

    mbs = size / 1000000
    rounded = round(mbs, 2)
    return f"{rounded} MB"

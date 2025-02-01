SUFFIXES = {1: "st", 2: "nd", 3: "rd"}


def get_ordinal_suffix(i: int) -> str:
    if 10 <= i % 100 <= 20:
        return "th"
    else:
        return SUFFIXES.get(i % 10, "th")

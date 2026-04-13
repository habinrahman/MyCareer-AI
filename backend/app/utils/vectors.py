def format_vector(values: list[float]) -> str:
    return "[" + ",".join(str(float(x)) for x in values) + "]"

import pytask


@pytask.hookimpl
def pytask_parse_config(config, config_from_file):
    markers = _read_marker_mapping_from_ini(config_from_file.get("markers", ""))
    config["markers"] = {**markers, **config["markers"]}


def _read_marker_mapping_from_ini(string: str) -> dict:
    # Split by newlines and remove empty strings.
    lines = filter(lambda x: bool(x), string.split("\n"))
    mapping = {}
    for line in lines:
        try:
            key, value = line.split(":")
        except ValueError as e:
            key = line
            value = ""
            if not key.isidentifier():
                raise ValueError(
                    f"{key} is not a valid Python name and cannot be used as a marker."
                ) from e

        mapping[key] = value

    return mapping

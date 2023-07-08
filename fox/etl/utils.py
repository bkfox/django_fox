from jsonpath2.path import Path as JSONPath


def as_json_path(path, allow_none=False):
    """Return provided path as json path."""
    if isinstance(path, str):
        return JSONPath.parse_str(path)
    elif isinstance(path, JSONPath):
        return path
    elif allow_none and path is None:
        return None
    raise ValueError("invalid path {} (type: {})".format(path, type(path)))


def get_data(self, data, path, many=False, with_path=False):
    """Return data using provided path, as `(json_path, data)`.

    :param data: input data
    :param JsonPath path: target path
    :param bool many: return an array instead the first matching value
    :param with_path: for each match, return a tuple of ``(path, value)``.
    """
    if not path:
        return data

    if with_path:
        iter = (
            (m.node.tojsonpath(), m.current_value) for m in path.match(data)
        )
    else:
        iter = (m.current_value for m in path.match(data))
    return list(iter) if many else next(iter, None)

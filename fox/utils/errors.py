"""
Provide errors and exception utilities.
"""


__all__ = ('Errors',)


class Errors(Exception):
    """
    Raise multiple errors at once, using `errors` attribute.

    Can be used as a context manager such as:

        ```
        with Errors('multiple errors occurred') as errors:
            # errors.append(exception)
            # raise ValueError('test exceptions')
        ```
    """

    def __init__(self, *a, errors=None, **kw):
        self.errors = errors or []
        super().__init__(*a, **kw)

    def __enter__(self):
        return self.errors

    def __exit__(self, type, value, traceback):
        if type:
            self.errors.append((value, traceback))
        if self.errors:
            raise self

    def __str__(self):
        errors = [r if isinstance(r, Exception) else '{}\n{}\n'.join(r)
                  for r in self.errors]
        return self.message + ':\n    ' + '\n    '.join(errors) 



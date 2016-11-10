# import from this module

from apiclient import errors

__all__ = ['unwrap_pages']

class UnwrapError(Exception):
    pass


def unwrap_pages(func):
    def wrapper(self, **kwargs):
        result = []
        page_token = None
        while True:
            try:
                param = {}
                if page_token:
                    param['pageToken'] = page_token
                kwargs.update(param)
                lkwargs = kwargs.copy()
                part = func(self, **lkwargs)
                result.extend(part.get('items', []))
                page_token = part.get('nextPageToken')
                if not page_token:
                    break
            except errors.HttpError as error:
                raise UnwrapError('%s(): HttpError while '
                            'unwrapping %s' % (func.func_name, error))
        return result
    wrapper.__doc__ = func.__doc__
    wrapper.__name__ = func.__name__
    return wrapper
            
        

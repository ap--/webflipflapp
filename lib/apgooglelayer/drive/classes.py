# import from this module
from .extras import SimpleTree, HashableIdDict
from ..common import unwrap_pages
from apiclient.discovery import build

__all__ = ['GoogleDrive', 'GoogleDriveError']


class GoogleDriveError(Exception):
    pass


class GoogleDrive(object):
    icon = 'https://developers.google.com/drive/images/drive_icon.png'

    def __init__(self, service=None):
        if service is None:
            self.service = build('drive', 'v2')
        else:
            self.service = service

    def about(self, **kwargs):
        http = kwargs.pop('http', None)
        return self.service.about().get(**kwargs).execute(http=http)

    @unwrap_pages
    def all_files(self, **kwargs):
        http = kwargs.pop('http', None)
        return self.service.files().list(**kwargs).execute(http=http)

    @unwrap_pages
    def files_in_folder(self, **kwargs):
        http = kwargs.pop('http', None)
        return self.service.children().list(**kwargs).execute(http=http)

    def folder_structure(self, http=None, fields=None):
        _fields = ('items(title,id,mimeType,parents/id,'
                   'parents/isRoot)')
        if fields is not None:
            _fields += ',%s' % fields
        #XXX: TODO: check for required fields      

        # This limits the search to untrashed spreadsheets and folders.
        # if there are too many files, the previous way of iterating
        # over everything caused errors...
        myquery = ("trashed = false and "
                   "(mimeType = 'application/vnd.google-apps.spreadsheet' or "
                   "mimeType = 'application/vnd.google-apps.folder')")
        # DATA: all spreadsheets and folders that are not deleted
        DATA = self.all_files(http=http, fields=_fields, q=myquery)

        # try to guess root_id:
        GUESS = []
        for d in DATA:
            for p in d['parents']:
                if p['isRoot']:
                    GUESS.append(p['id'])
        GUESS = set(GUESS) # if there's only one possible solution, we're done.
        if len(GUESS) == 1:
            root_id, = GUESS
        elif len(GUESS) > 1:
            root_id = self.about(http=http,
                    fields='rootFolderId').pop('rootFolderId')
        else:
            raise GoogleDriveError("can't build tree without root!")

        # sort'em
        def recurse(START, T):
            # get all files, that have START as a parent
            TRACK = []
            N = len(DATA)
            for i,d in enumerate(reversed(DATA)):
                if any(p['id'] == START for p in d['parents']):
                    TRACK.append(DATA.pop(N-i-1))

            for f in TRACK:
                Hid = HashableIdDict(**f)
                T[Hid] # creates entry through defaultdict
                if 'folder' in f['mimeType']:
                    recurse(START=f['id'], T=T[Hid])

        Tree = SimpleTree()
        recurse(root_id, Tree)
        return Tree


    def files_as_id_dict(self, http=None, **kwargs):
        FILES = self.all_files(http=http, **kwargs)
        return {f['id']: f for f in FILES}
        

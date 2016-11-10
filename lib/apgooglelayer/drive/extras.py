#!/usr/bin/python

import collections


class HashableIdDict(dict):
    
    def __init__(self, *args, **kwargs):
        """HashableIdDict(**kwargs)

        provide keyword parameter 'id' that is going to be used as the
        hashable object.
        provide extra kwargs that are going to be added to the dict.

        required kwarg:
            id : any immutable object
        extra kwargs:
            ...

        the 'id' value can't be changed.

        returns a HashableIdDict
        """
        sn = self.__class__.__name__
        if len(args) > 0:
            raise TypeError("%s.__init__(): takes only keyword arguments" % sn)
        if 'id' not in kwargs.keys():
            raise TypeError("%s.__init__(): attribute id must be provided" % sn)
        try:
            hash(kwargs.get('id'))
        except TypeError:
            raise TypeError("%s.__init__(): requires immutable object for id" % sn)
        super(HashableIdDict, self).__init__(**kwargs)

    def __setitem__(self, i, y):
        if i == 'id':
            raise TypeError("%s: item id can not be changed" % self.__class__.__name__)
        super(HashableIdDict, self).__setitem__(i, y)

    __hash__ = lambda self: hash(self['id'])
    __eq__ = lambda self, other: self['id'] == other['id']
    __repr__ = lambda x: 'HashableIdDict(%s)' % super(HashableIdDict, x).__repr__()
    __str__ = lambda x: 'HashableIdDict(%s)' % super(HashableIdDict, x).__str__()



class SimpleTree(collections.defaultdict):

    def __init__(self):
        super(SimpleTree, self).__init__(SimpleTree)

    def walkthrough(self, key=None, filter=None):
        """walkthrough(key=None)

        walk through all files in tree.
        return level, node

        optional key argument can be used for sorting:
 
        > sort by 'title'
        key = lambda x: x['title']

        > sort first by 'a', then by 'b'
        key = lambda x: (x['a'], x['b'])
        """
        def recurse(treenode, level, key=None):
            for hashable_item in sorted(treenode.keys(), key=key):
                childnode = treenode[hashable_item]
                if hasattr(filter, '__call__'):
                    if filter(hashable_item):
                        yield level, hashable_item
                else:
                    yield level, hashable_item
                for l,h in recurse(childnode, level+1, key=key):
                    yield l,h
        return recurse(self, 0, key=key)

    def flat(self, key=None, filter=None):
        """flat(key=None)

        see walkthrough.

        returns only nodes
        """
        FLAT = [k for l,k in self.walkthrough(key)]
        return FLAT

    def flatten_names(self, key=None, filter=None):
        prefix = ['']
        for l,v in self.walkthrough(key=key):
            prefix = prefix[:l+1] + [v['title']]
            if hasattr(filter, '__call__'):
                if filter(v):
                    yield "/".join(prefix), v
            else:
                yield "/".join(prefix), v



    def get_all_where(self, selectfunc):
        return (k for k in self.flat() if selectfunc(k))

    def get_first_where(self, selectfunc):
        return next(self.get_all_where(selectfunc))








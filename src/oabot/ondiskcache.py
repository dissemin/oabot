# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import cPickle
from os.path import isfile

class OnDiskCache(object):
    def __init__(self, path):
        self.path = path
        self.store = {}
        self.ttl = datetime.timedelta(days=365)
        if path:
            self.load()

    def load(self):
        if isfile(self.path):
            with open(self.path, 'rb') as f:
                self.store = cPickle.load(f)
        else:
            self.store = {}
            with open(self.path, 'wb') as f:
                cPickle.dump(self.store, f)

    def fresh(self, date):
        return date+self.ttl > datetime.date.today()

    def prune(self):
        for k in list(self.store.keys()):
            d, v = self.store[k]
            if not self.fresh(d):
                del self.store[k]

    def save(self, reload_before=True):
        if reload_before:
            new_store = {}
            with open(self.path, 'rb') as f:
                new_store = cPickle.load(f)
            self.store.update(new_store)
        
        self.prune()

        with open(self.path, 'wb') as f:
            cPickle.dump(self.store, f)

    def __contains__(self, url):
        return url in self.store and self.fresh(self.store[url][0])
    
    def get(self, url):
        if url in self:
            return self.store[url][1]
        
    def set(self, url, val):
        self.store[url] = (datetime.date.today(), val)

    def print_contents(self):
        for k in self.store:
            print '\t'.join([unicode(self.store[k][1]), k])

    def cached(self, fun):
        def new_fun(arg):
            cur_val = self.get(arg)
            if cur_val is not None:
                return cur_val
            new_val = fun(arg)
            self.set(arg, new_val)
            return new_val
        return new_fun
 

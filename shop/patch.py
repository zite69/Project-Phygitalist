from importlib import import_module
import sys


class PatchedModuleFinder(object):
    is_deperate = False
    def find_module(self, fullname, path=None):
        if fullname not in ('account.decorators'):
            return None
        is_after = False
        for finder in sys.meta_path:
            if not is_after:
                is_after = finder is self
                continue
            loader = finder.find_module(fullname, path)
            if loader is not None:
                return PatchedLoader(fullname, loader)


class PatchedLoader(object):
    def __init__(self, fullname, main_loader) -> None:
        self.fullname = fullname
        self.main_loader = main_loader

    def load_module(self, fullname):
        if self.main_loader is not None:
            module = self.main_loader.load_module(fullname)
        else:
            module = import_module(fullname)
            PatchedModuleFinder.is_desperate = False
        if fullname == 'account.decorators':
            from django.contrib.auth.decorators import login_required
            module.login_required = login_required

        return module

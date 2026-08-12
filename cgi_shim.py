"""Fake cgi module for Python 3.14 compatibility.

This module was removed in Python 3.14, but some older packages
(e.g., Cython 0.29.x) still import it.
"""
import warnings
warnings.warn("The cgi module is deprecated and was removed in Python 3.14. "
              "This is a compatibility shim.", DeprecationWarning, stacklevel=2)

def parse_header(line):
    """Parse a Content-type like header.
    
    Return the main content-type and a dictionary of options.
    """
    parts = line.split(';')
    key = parts[0].strip()
    pdict = {}
    for part in parts[1:]:
        if '=' in part:
            name, value = part.split('=', 1)
            pdict[name.strip()] = value.strip().strip('"')
    return key, pdict

def parse_multipart(fp, pdict, encoding='utf-8', errors='replace'):
    """Parse multipart form data."""
    return {}

def parse_qs(qs, keep_blank_values=False, strict_parsing=False, encoding='utf-8', errors='replace'):
    """Parse a query string."""
    from urllib.parse import parse_qs as _parse_qs
    return _parse_qs(qs, keep_blank_values, strict_parsing, encoding=encoding, errors=errors)

# Minimal FieldStorage for compatibility
class FieldStorage:
    def __init__(self, fp=None, headers=None, outerboundary=b'', environ=None, keep_blank_values=0, strict_parsing=0, limit=None, encoding='utf-8', errors='replace'):
        import os
        if environ is None:
            environ = os.environ
        self.list = []
        self.name = None
        self.filename = None
        self.value = None
        self.file = None
        self.type = None
        self.type_options = {}
        self.disposition = None
        self.disposition_options = {}
        self.headers = {}
        
    def __getitem__(self, key):
        for item in self.list:
            if item.name == key:
                return item
        raise KeyError(key)
        
    def __contains__(self, key):
        return any(item.name == key for item in self.list)
        
    def getvalue(self, key, default=None):
        for item in self.list:
            if item.name == key:
                return item.value
        return default
        
    def getfirst(self, key, default=None):
        return self.getvalue(key, default)
        
    def getlist(self, key):
        return [item.value for item in self.list if item.name == key]

    def __bool__(self):
        return bool(self.list)

__all__ = ['parse_header', 'parse_multipart', 'parse_qs', 'FieldStorage']

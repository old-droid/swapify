import requests

CRATE_API = "https://crates.io/api/v1/crates"
DEFAULT_MAP = {
    'numpy': 'ndarray', 'pandas': 'polars', 'requests': 'reqwest', 'flask': 'actix-web',
    'django': 'actix-web', 'matplotlib': 'plotters', 'sklearn': 'linfa', 'json': 'serde_json',
    'os': 'std::fs', 'sys': 'std::env', 'collections': 'std::collections', 'pathlib': 'std::path',
    'datetime': 'chrono', 're': 'regex', 'math': 'libm', 'random': 'rand', 'sqlite3': 'rusqlite',
    'subprocess': 'std::process', 'asyncio': 'tokio', 'threading': 'std::thread', 'csv': 'csv',
    'logging': 'log', 'argparse': 'clap', 'pickle': 'serde', 'hashlib': 'sha2', 'hmac': 'hmac',
    'base64': 'base64', 'urllib': 'url', 'glob': 'glob', 'shutil': 'std::fs', 'tempfile': 'tempfile',
    'decimal': 'bigdecimal', 'statistics': 'statrs', 'xml': 'quick-xml', 'email': 'lettre',
    'http': 'hyper', 'socket': 'tokio', 'ssl': 'native-tls', 'uuid': 'uuid', 'enum': 'strum',
}
STD_CRATES = {'std::fs', 'std::env', 'std::path', 'std::collections', 'std::process', 'std::thread'}


class LibraryMapper:
    def __init__(self, use_api=True):
        self.use_api = use_api
        self.custom = dict(DEFAULT_MAP)

    def map_library(self, lib_name):
        if not lib_name:
            return {'crate': '', 'note': ''}
        key = lib_name.lower().split('.')[0]
        if key in self.custom:
            return {'crate': self.custom[key], 'note': ''}
        if self.use_api:
            return self._search(key)
        return {'crate': '', 'note': 'unknown'}

    def _search(self, q):
        try:
            r = requests.get(CRATE_API, params={'q': q, 'per_page': 1}, timeout=3, headers={'User-Agent': 'swapify/0.1'})
            if r.status_code == 200:
                j = r.json()
                crates = j.get('crates', [])
                if crates:
                    return {'crate': crates[0]['name'], 'note': crates[0].get('description', '')[:60]}
        except Exception:
            pass
        return {'crate': '', 'note': 'not found'}

    def map_imports(self, imports):
        out = []
        for imp in imports:
            if imp['type'] == 'import':
                for n in imp['names']:
                    out.append({'import': n, **self.map_library(n)})
            else:
                mod = imp['module'] or ''
                out.append({'import': mod, 'names': imp['names'], **self.map_library(mod)})
        return out

    def add_mapping(self, py_lib, crate, note=''):
        self.custom[py_lib] = crate

    def get_cargo_deps(self, mappings):
        deps = []
        for m in mappings:
            c = m.get('crate', '')
            if c and c not in STD_CRATES and '::' not in c:
                deps.append({'name': c, 'import': m.get('import', c)})
        seen = {}
        for d in deps:
            seen[d['name']] = d
        return list(seen.values())

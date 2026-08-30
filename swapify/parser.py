import ast
import re


class Parser:
    def parse_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
        except Exception as e:
            return {'imports': [], 'functions': [], 'classes': [], 'variables': [], 'source': '', 'filepath': filepath, 'error': str(e)}
        try:
            tree = ast.parse(source, filename=filepath)
        except SyntaxError as e:
            return {'imports': [], 'functions': [], 'classes': [], 'variables': [], 'source': source, 'filepath': filepath, 'error': 'SyntaxError: {}'.format(e)}
        self.imports, self.functions, self.classes, self.variables = [], [], [], []
        self._walk(tree)
        return {'imports': self.imports, 'functions': self.functions, 'classes': self.classes, 'variables': self.variables, 'source': source, 'filepath': filepath, 'error': None}

    def _walk(self, node):
        if isinstance(node, ast.Import):
            self.imports.append({'type': 'import', 'names': [a.name for a in node.names]})
        elif isinstance(node, ast.ImportFrom):
            self.imports.append({'type': 'from', 'module': node.module, 'names': [a.name for a in node.names]})
        elif isinstance(node, ast.FunctionDef):
            self.functions.append({'name': node.name, 'args': self._extract_args(node.args.args), 'returns': self._get_returns(node.returns), 'body': self._extract_body(node.body)})
        elif isinstance(node, ast.ClassDef):
            methods, body = [], []
            for n in node.body:
                if isinstance(n, ast.FunctionDef):
                    methods.append({'name': n.name, 'args': self._extract_args(n.args.args), 'returns': self._get_returns(n.returns), 'body': self._extract_body(n.body)})
                else:
                    try:
                        body.append(ast.unparse(n))
                    except Exception:
                        pass
            self.classes.append({'name': node.name, 'bases': [self._get_base(b) for b in node.bases], 'methods': methods, 'body': body})
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(target, ast.Name):
                try:
                    v = ast.unparse(node.value) if node.value else 'None'
                except Exception:
                    v = 'None'
                self.variables.append({'name': target.id, 'value': v})
        for child in ast.iter_child_nodes(node):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                continue
            self._walk(child)

    def _extract_args(self, args):
        out = []
        for a in args:
            t = self._get_annotation(a.annotation) if a.annotation else 'dynamic'
            out.append({'name': a.arg, 'type': t})
        return out

    def _get_annotation(self, node):
        try:
            return self._py_type_to_rust(ast.unparse(node))
        except Exception:
            return 'dynamic'

    def _py_type_to_rust(self, t):
        m = {'str': 'String', 'int': 'i64', 'float': 'f64', 'bool': 'bool', 'bytes': 'Vec<u8>', 'list': 'Vec<String>', 'dict': 'HashMap<String,String>', 'List': 'Vec<String>', 'Dict': 'HashMap<String,String>'}
        for k, v in m.items():
            if t.startswith(k):
                return v
        return t

    def _extract_body(self, body):
        out = []
        for s in body:
            try:
                out.append(ast.unparse(s))
            except Exception:
                pass
        return out

    def _get_returns(self, node):
        if node is None:
            return None
        try:
            return self._py_type_to_rust(ast.unparse(node))
        except Exception:
            return None

    def _get_base(self, node):
        try:
            return ast.unparse(node)
        except Exception:
            return ''

    def find_pattern(self, source, pattern):
        return re.findall(pattern, source)

    def get_all_source(self, filepath):
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

"""
Módulo de chunking semântico por linguagem.

Responsável por dividir o conteúdo de arquivos em chunks,
respeitando a estrutura sintática de cada linguagem de programação.

Camada 1 — chunking semântico dedicado:   .py, .java, .js, .ts, .sql
Camada 2 — chunking por blocos brace {}:  .go, .cs, .kt, .cpp, .c, .h, .rs, .php, .scala, .swift, .m
Camada 3 — chunking por blocos end:       .rb
Camada 4 — fallback por tamanho fixo:     qualquer outra extensão
"""

import ast
import re

from minorag import config as _cfg

_JAVA_SIG = re.compile(
    r"^\s*(?:(?:public|private|protected|static|final|abstract|"
    r"synchronized|native|default|strictfp)\s+)*"
    r"(?:class|interface|enum|record|@interface|\w[\w<>\[\],\s]*)\s+\w+\s*[({<]",
    re.MULTILINE,
)

_JS_SIG = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?"
    r"(?:function[\s*]+\w+|class\s+\w+|(?:const|let|var)\s+\w+\s*=)",
    re.MULTILINE,
)

_GO_SIG = re.compile(
    r"^\s*(?:func\s+(?:\(\w+\s+\*?\w+\)\s+)?\w+|type\s+\w+\s+struct)\s*[({]",
    re.MULTILINE,
)

_C_SIG = re.compile(
    r"^\s*(?:(?:static|inline|extern|const|unsigned|signed|struct|enum|union|"
    r"typedef|void|int|char|float|double|long|short|bool|auto)\s+)*"
    r"\w[\w\s*&<>:]*\w+\s*\([^;]*\)\s*\{",
    re.MULTILINE,
)

_CS_SIG = re.compile(
    r"^\s*(?:(?:public|private|protected|internal|static|virtual|override|"
    r"abstract|sealed|async|partial|readonly|new)\s+)*"
    r"(?:class|interface|struct|enum|record|\w[\w<>\[\],\s]*)\s+\w+\s*[({<]",
    re.MULTILINE,
)

_RS_SIG = re.compile(
    r"^\s*(?:pub(?:\(crate\))?\s+)?(?:fn|impl|struct|enum|trait|mod)\s+\w+",
    re.MULTILINE,
)

_KT_SIG = re.compile(
    r"^\s*(?:(?:public|private|protected|internal|open|abstract|sealed|"
    r"data|inline|suspend|override)\s+)*"
    r"(?:fun|class|object|interface)\s+\w+",
    re.MULTILINE,
)

_PHP_SIG = re.compile(
    r"^\s*(?:(?:public|private|protected|static|abstract|final)\s+)*"
    r"(?:function|class|interface|trait|enum)\s+\w+",
    re.MULTILINE,
)

_SCALA_SIG = re.compile(
    r"^\s*(?:(?:private|protected|override|abstract|sealed|final|lazy|implicit)\s+)*"
    r"(?:def|class|object|trait|case\s+class)\s+\w+",
    re.MULTILINE,
)

_SWIFT_SIG = re.compile(
    r"^\s*(?:(?:public|private|internal|open|fileprivate|static|class|override|"
    r"mutating|final)\s+)*"
    r"(?:func|class|struct|enum|protocol|extension)\s+\w+",
    re.MULTILINE,
)

_END_BLOCK_SIG = re.compile(
    r"^\s*(?:def|class|module)\s+\w+", re.MULTILINE
)

_BRACE_SIGS: dict[str, re.Pattern[str]] = {
    ".java":  _JAVA_SIG,
    ".js":    _JS_SIG,
    ".ts":    _JS_SIG,
    ".go":    _GO_SIG,
    ".c":     _C_SIG,
    ".cpp":   _C_SIG,
    ".h":     _C_SIG,
    ".cs":    _CS_SIG,
    ".rs":    _RS_SIG,
    ".kt":    _KT_SIG,
    ".php":   _PHP_SIG,
    ".scala": _SCALA_SIG,
    ".swift": _SWIFT_SIG,
    ".m":     _C_SIG,
}


def chunk_text(text: str) -> list[str]:
    """Divide um texto em chunks de tamanho fixo com sobreposição (fallback)."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start: start + _cfg.CHUNK_SIZE])
        start += _cfg.CHUNK_SIZE - _cfg.CHUNK_OVERLAP
    return chunks


def _extract_brace_blocks(source: str, sig_re: re.Pattern[str]) -> list[str]:
    """Extrai blocos { } que iniciam com uma assinatura reconhecida."""
    lines = source.splitlines(keepends=True)
    blocks: list[str] = []
    used: set[int] = set()

    for m in sig_re.finditer(source):
        start_line = source[: m.start()].count("\n")
        if start_line in used:
            continue

        depth = 0
        found_open = False
        block: list[str] = []

        for i, line in enumerate(lines[start_line:], start=start_line):
            block.append(line)
            for ch in line:
                if ch == "{":
                    depth += 1
                    found_open = True
                elif ch == "}":
                    depth -= 1
            if found_open and depth <= 0:
                for j in range(start_line, i + 1):
                    used.add(j)
                blocks.append("".join(block))
                break

    return blocks if blocks else chunk_text(source)


def _extract_end_blocks(source: str) -> list[str]:
    """Extrai blocos def/class...end para Ruby."""
    lines = source.splitlines(keepends=True)
    blocks: list[str] = []
    used: set[int] = set()

    for m in _END_BLOCK_SIG.finditer(source):
        start_line = source[: m.start()].count("\n")
        if start_line in used:
            continue

        depth = 0
        block: list[str] = []

        for i, line in enumerate(lines[start_line:], start=start_line):
            block.append(line)
            stripped = line.strip()
            if re.match(r"(def|class|module|do|if|unless|case|while|until|for|begin)\b", stripped):
                depth += 1
            if stripped == "end" or stripped.startswith("end "):
                depth -= 1
            if depth <= 0 and len(block) > 1:
                for j in range(start_line, i + 1):
                    used.add(j)
                blocks.append("".join(block))
                break

    return blocks if blocks else chunk_text(source)


def _chunk_python(source: str) -> list[str]:
    """Chunking semântico para Python via AST."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return chunk_text(source)

    lines = source.splitlines(keepends=True)
    chunks: list[str] = []

    def _src(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> str:
        return "".join(lines[node.lineno - 1: node.end_lineno])

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            chunks.append(_src(node))
        elif isinstance(node, ast.ClassDef):
            full = _src(node)
            if len(full) <= _cfg.CHUNK_SIZE * 2:
                chunks.append(full)
            else:
                first_child = node.body[0].lineno - 1
                chunks.append("".join(lines[node.lineno - 1: first_child]))
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        chunks.append(_src(child))

    return chunks if chunks else chunk_text(source)


def _chunk_sql(source: str) -> list[str]:
    """Divide SQL por statements terminados em ';'."""
    statements = re.split(r";\s*(?:\n|$)", source, flags=re.MULTILINE)
    return [s.strip() for s in statements if len(s.strip()) > 20]


def chunk_by_language(source: str, ext: str) -> list[str]:
    """
    Despacha para o chunker adequado conforme a extensão do arquivo.

    @param source: Conteúdo do arquivo.
    @param ext: Extensão do arquivo (ex: '.py', '.java').
    @return: Lista de chunks semânticos ou por tamanho fixo.
    """
    if ext == ".py":
        return _chunk_python(source)
    if ext == ".sql":
        return _chunk_sql(source)
    if ext == ".rb":
        return _extract_end_blocks(source)
    if ext in _BRACE_SIGS:
        return _extract_brace_blocks(source, _BRACE_SIGS[ext])
    return chunk_text(source)

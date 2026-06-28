"""
GBNF grammar used to constrain llama.cpp's decoding so the model literally cannot
emit syntactically invalid JSON.

Scope note (read this before "fixing" it): this is a *generic JSON-value* grammar,
not a per-field schema-aware grammar (i.e. it guarantees valid JSON syntax, not that
the right keys/types appear). Full schema-aware GBNF generation — emitting a grammar
rule per Pydantic field, with the exact key order and value types locked in — is a
real stretch goal (see spec-kit/plan.md "Stretch goals"), not faked here as something
it isn't. Semantic correctness (right keys, right types) is enforced afterwards by
`validate.py` against the Pydantic schema; if the LLM's syntactically-valid JSON is
semantically wrong, that's a `needs_review` flag, not a silent pass.
"""

from __future__ import annotations

# Adapted from llama.cpp's bundled grammars/json.gbnf (MIT-licensed grammar definition
# shipped with llama.cpp itself) — reproduced here so this repo has no runtime
# dependency on locating that file inside whatever llama.cpp install the user has.
JSON_GRAMMAR = r"""
root   ::= object
value  ::= object | array | string | number | ("true" | "false" | "null")

object ::=
  "{" ws (
            string ":" ws value
    ("," ws string ":" ws value)*
  )? "}" ws

array  ::=
  "[" ws (
            value
    ("," ws value)*
  )? "]" ws

string ::=
  "\"" (
    [^"\\\x7F\x00-\x1F] |
    "\\" (["\\bfnrt] | "u" [0-9a-fA-F]{4})
  )* "\"" ws

number ::= ("-"? ([0-9] | [1-9] [0-9]{0,15})) ("." [0-9]+)? ([eE] [-+]? [0-9]+)? ws

ws ::= [ \t\n]*
"""


def generic_json_grammar() -> str:
    """Return the GBNF grammar text. Pass this to llama_cpp.LlamaGrammar.from_string(...)."""
    return JSON_GRAMMAR

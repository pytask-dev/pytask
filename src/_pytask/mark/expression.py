r"""Evaluate match expressions, as used by `-k` and `-m`.

The grammar is:

expression: expr? EOF
expr:       and_expr ('or' and_expr)*
and_expr:   not_expr ('and' not_expr)*
not_expr:   'not' not_expr | '(' expr ')' | ident kwargs?

ident:      (\w|:|\+|-|\.|\[|\]|\\|/)+
kwargs:     ('(' name '=' value (', ' name '=' value)* ')')
name:       a valid identifier that is not a reserved keyword
value:      unescaped string literal | (-)?[0-9]+ | 'False' | 'True' | 'None'

The semantics are:

- Empty expression evaluates to False.
- ident evaluates to True or False according to a provided matcher function.
- ident with keyword arguments evaluates to True or False according to a provided
  matcher function.
- or/and/not evaluate according to the usual boolean semantics.

This module is adapted from pytest's ``_pytest.mark.expression`` module:
https://github.com/pytest-dev/pytest/blob/main/src/_pytest/mark/expression.py

"""

from __future__ import annotations

import ast
import enum
import keyword
import re
from collections.abc import Iterator
from collections.abc import Mapping
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Protocol

if TYPE_CHECKING:
    import types
    from typing import NoReturn


__all__ = ["Expression", "ExpressionMatcher"]


FILE_NAME = "<pytask match expression>"


class TokenType(enum.Enum):
    LPAREN = "left parenthesis"
    RPAREN = "right parenthesis"
    OR = "or"
    AND = "and"
    NOT = "not"
    IDENT = "identifier"
    EOF = "end of input"
    EQUAL = "="
    STRING = "string literal"
    COMMA = ","


@dataclass(frozen=True, slots=True)
class Token:
    type_: TokenType
    value: str
    pos: int


class Scanner:
    __slots__ = ("current", "idents", "input", "tokens")

    def __init__(self, input_: str) -> None:
        self.idents: set[str] = set()
        self.input = input_
        self.tokens = self.lex(input_)
        self.current = next(self.tokens)

    def lex(self, input_: str) -> Iterator[Token]:  # noqa: C901, PLR0912
        pos = 0
        while pos < len(input_):
            if input_[pos] in (" ", "\t"):
                pos += 1
            elif input_[pos] == "(":
                yield Token(TokenType.LPAREN, "(", pos)
                pos += 1
            elif input_[pos] == ")":
                yield Token(TokenType.RPAREN, ")", pos)
                pos += 1
            elif input_[pos] == "=":
                yield Token(TokenType.EQUAL, "=", pos)
                pos += 1
            elif input_[pos] == ",":
                yield Token(TokenType.COMMA, ",", pos)
                pos += 1
            elif (quote_char := input_[pos]) in ("'", '"'):
                end_quote_pos = input_.find(quote_char, pos + 1)
                if end_quote_pos == -1:
                    msg = f'closing quote "{quote_char}" is missing'
                    raise SyntaxError(
                        msg,
                        (FILE_NAME, 1, pos + 1, input_),
                    )
                value = input_[pos : end_quote_pos + 1]
                if (backslash_pos := value.find("\\")) != -1:
                    msg = r'escaping with "\" not supported in marker expression'
                    raise SyntaxError(
                        msg,
                        (FILE_NAME, 1, pos + backslash_pos + 1, input_),
                    )
                yield Token(TokenType.STRING, value, pos)
                pos += len(value)
            else:
                match = re.match(r"(:?\w|:|\+|-|\.|\[|\]|/|\\)+", input_[pos:])
                if match:
                    value = match.group(0)
                    if value == "or":
                        yield Token(TokenType.OR, value, pos)
                    elif value == "and":
                        yield Token(TokenType.AND, value, pos)
                    elif value == "not":
                        yield Token(TokenType.NOT, value, pos)
                    else:
                        yield Token(TokenType.IDENT, value, pos)
                    pos += len(value)
                else:
                    msg = f'unexpected character "{input_[pos]}"'
                    raise SyntaxError(
                        msg,
                        (FILE_NAME, 1, pos + 1, input_),
                    )
        yield Token(TokenType.EOF, "", pos)

    def accept(self, type_: TokenType, *, reject: bool = False) -> Token | None:
        if self.current.type_ is type_:
            token = self.current
            if token.type_ is not TokenType.EOF:
                self.current = next(self.tokens)
            return token
        if reject:
            self.reject((type_,))
        return None

    def reject(self, expected: Sequence[TokenType]) -> NoReturn:
        msg = "expected {}; got {}".format(
            " OR ".join(type_.value for type_ in expected),
            self.current.type_.value,
        )
        raise SyntaxError(
            msg,
            (FILE_NAME, 1, self.current.pos + 1, self.input),
        )


# True, False and None are legal match expression identifiers, but illegal as Python
# identifiers. To fix this, this prefix is added to identifiers in the conversion to
# Python AST.
IDENT_PREFIX = "$"


def expression(s: Scanner) -> tuple[ast.Expression, frozenset[str]]:
    if s.accept(TokenType.EOF):
        ret: ast.expr = ast.Constant(False)
    else:
        ret = expr(s)
        s.accept(TokenType.EOF, reject=True)
    return ast.fix_missing_locations(ast.Expression(ret)), frozenset(s.idents)


def expr(s: Scanner) -> ast.expr:
    ret = and_expr(s)
    while s.accept(TokenType.OR):
        rhs = and_expr(s)
        ret = ast.BoolOp(ast.Or(), [ret, rhs])
    return ret


def and_expr(s: Scanner) -> ast.expr:
    ret = not_expr(s)
    while s.accept(TokenType.AND):
        rhs = not_expr(s)
        ret = ast.BoolOp(ast.And(), [ret, rhs])
    return ret


def not_expr(s: Scanner) -> ast.expr:
    if s.accept(TokenType.NOT):
        return ast.UnaryOp(ast.Not(), not_expr(s))
    if s.accept(TokenType.LPAREN):
        ret = expr(s)
        s.accept(TokenType.RPAREN, reject=True)
        return ret
    ident = s.accept(TokenType.IDENT)
    if ident:
        s.idents.add(ident.value)
        name = ast.Name(IDENT_PREFIX + ident.value, ast.Load())
        if s.accept(TokenType.LPAREN):
            ret = ast.Call(func=name, args=[], keywords=all_kwargs(s))
            s.accept(TokenType.RPAREN, reject=True)
        else:
            ret = name
        return ret
    s.reject((TokenType.NOT, TokenType.LPAREN, TokenType.IDENT))
    return None  # ty: ignore[invalid-return-type]  # Unreachable: reject() raises


BUILTIN_MATCHERS = {"True": True, "False": False, "None": None}


def single_kwarg(s: Scanner) -> ast.keyword:
    """Parse one keyword argument."""
    keyword_name = s.accept(TokenType.IDENT, reject=True)
    assert keyword_name is not None
    if not keyword_name.value.isidentifier():
        msg = f"not a valid python identifier {keyword_name.value}"
        raise SyntaxError(
            msg,
            (FILE_NAME, 1, keyword_name.pos + 1, s.input),
        )
    if keyword.iskeyword(keyword_name.value):
        msg = f"unexpected reserved python keyword `{keyword_name.value}`"
        raise SyntaxError(
            msg,
            (FILE_NAME, 1, keyword_name.pos + 1, s.input),
        )
    s.accept(TokenType.EQUAL, reject=True)

    if value_token := s.accept(TokenType.STRING):
        value: str | int | bool | None = value_token.value[1:-1]
    else:
        value_token = s.accept(TokenType.IDENT, reject=True)
        assert value_token is not None
        if (number := value_token.value).isdigit() or (
            number.startswith("-") and number[1:].isdigit()
        ):
            value = int(number)
        elif value_token.value in BUILTIN_MATCHERS:
            value = BUILTIN_MATCHERS[value_token.value]
        else:
            msg = f'unexpected character/s "{value_token.value}"'
            raise SyntaxError(
                msg,
                (FILE_NAME, 1, value_token.pos + 1, s.input),
            )

    return ast.keyword(keyword_name.value, ast.Constant(value))


def all_kwargs(s: Scanner) -> list[ast.keyword]:
    """Parse all keyword arguments."""
    kwargs = [single_kwarg(s)]
    while s.accept(TokenType.COMMA):
        kwargs.append(single_kwarg(s))
    return kwargs


class ExpressionMatcher(Protocol):
    """Match an identifier and optional keyword arguments."""

    def __call__(self, name: str, /, **kwargs: str | int | bool | None) -> bool: ...


@dataclass
class MatcherNameAdapter:
    """Adapt one matcher name to boolean and callable expression forms."""

    matcher: ExpressionMatcher
    name: str

    def __bool__(self) -> bool:
        return self.matcher(self.name)

    def __call__(self, **kwargs: str | int | bool | None) -> bool:
        return self.matcher(self.name, **kwargs)


class MatcherAdapter(Mapping[str, MatcherNameAdapter]):
    """Adapts a matcher function to a locals mapping as required by eval()."""

    def __init__(self, matcher: ExpressionMatcher) -> None:
        self.matcher = matcher

    def __getitem__(self, key: str) -> MatcherNameAdapter:
        return MatcherNameAdapter(self.matcher, key[len(IDENT_PREFIX) :])

    def __iter__(self) -> Iterator[str]:  # pragma: no cover
        raise NotImplementedError

    def __len__(self) -> int:  # pragma: no cover
        raise NotImplementedError


class Expression:
    """A compiled match expression as used by -k and -m.

    The expression can be evaluated against different matchers.

    """

    __slots__ = ("_has_keyword_arguments", "_idents", "code")

    def __init__(
        self,
        code: types.CodeType,
        idents: frozenset[str],
        has_keyword_arguments: bool,
    ) -> None:
        self.code = code
        self._idents = idents
        self._has_keyword_arguments = has_keyword_arguments

    @classmethod
    def compile_(cls, input_: str) -> Expression:
        """Compile a match expression.

        Parameters
        ----------
        input_: str
            The input expression - one line.

        """
        astexpr, idents = expression(Scanner(input_))
        code: types.CodeType = compile(
            astexpr,
            filename="<pytask match expression>",
            mode="eval",
        )
        has_keyword_arguments = any(
            isinstance(node, ast.Call) for node in ast.walk(astexpr)
        )
        return cls(code, idents, has_keyword_arguments)

    def idents(self) -> frozenset[str]:
        """Return all identifiers which appear in the expression."""
        return self._idents

    def has_keyword_arguments(self) -> bool:
        """Return whether the expression contains marker keyword arguments."""
        return self._has_keyword_arguments

    def evaluate(self, matcher: ExpressionMatcher) -> bool:
        """Evaluate the match expression.

        Parameters
        ----------
        matcher : Callable[[str], bool]
            Given an identifier, should return whether it matches or not. Should be
            prepared to handle arbitrary strings as input.

        Returns
        -------
        bool
            Whether the expression matches or not.

        """
        return bool(
            eval(  # noqa: S307
                self.code, {"__builtins__": {}}, MatcherAdapter(matcher)
            )
        )

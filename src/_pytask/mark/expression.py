r"""Evaluate match expressions, as used by `-k` and `-m`.

The grammar is:

+------------+--------------------------------------------+
| expression | expr? EOF                                  |
+------------+--------------------------------------------+
| expr       | and_expr ('or' and_expr)*                  |
+------------+--------------------------------------------+
| and_expr   | not_expr ('and' not_expr)*                 |
+------------+--------------------------------------------+
| not_expr   | ``'not' not_expr | '(' expr ')' | ident``  |
+------------+--------------------------------------------+
| ident      | ``(\w|:|\+|-|\.|\[|\]|\\)+``               |
+------------+--------------------------------------------+

The semantics are:

- Empty expression evaluates to False.
- ident evaluates to True of False according to a provided matcher function.
- or/and/not evaluate according to the usual boolean semantics.

"""
from __future__ import annotations

import ast
import enum
import re
import types
from typing import Callable
from typing import Iterator
from typing import Mapping
from typing import Sequence
from typing import TYPE_CHECKING

import attr


if TYPE_CHECKING:
    from typing import NoReturn


__all__ = ["Expression", "ParseError"]


class TokenType(enum.Enum):
    LPAREN = "left parenthesis"
    RPAREN = "right parenthesis"
    OR = "or"
    AND = "and"
    NOT = "not"
    IDENT = "identifier"
    EOF = "end of input"


@attr.s(frozen=True, slots=True)
class Token:
    type_ = attr.ib(type=TokenType)
    value = attr.ib(type=str)
    pos = attr.ib(type=int)


class ParseError(Exception):
    """The expression contains invalid syntax.

    Attributes
    ----------
    column : int
        The column in the line where the error occurred (1-based).
    message : str
        A description of the error.

    """

    def __init__(self, column: int, message: str) -> None:
        self.column = column
        self.message = message

    def __str__(self) -> str:
        return f"at column {self.column}: {self.message}"


class Scanner:
    __slots__ = ("tokens", "current")

    def __init__(self, input_: str) -> None:
        self.tokens = self.lex(input_)
        self.current = next(self.tokens)

    def lex(self, input_: str) -> Iterator[Token]:
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
                    raise ParseError(
                        pos + 1,
                        f'unexpected character "{input_[pos]}"',
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
        raise ParseError(
            self.current.pos + 1,
            "expected {}; got {}".format(
                " OR ".join(type_.value for type_ in expected),
                self.current.type_.value,
            ),
        )


# True, False and None are legal match expression identifiers, but illegal as Python
# identifiers. To fix this, this prefix is added to identifiers in the conversion to
# Python AST.
IDENT_PREFIX = "$"


def expression(s: Scanner) -> ast.Expression:
    if s.accept(TokenType.EOF):
        ret: ast.expr = ast.NameConstant(False)
    else:
        ret = expr(s)
        s.accept(TokenType.EOF, reject=True)
    return ast.fix_missing_locations(ast.Expression(ret))


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


def not_expr(s: Scanner) -> ast.expr | None:
    if s.accept(TokenType.NOT):
        return ast.UnaryOp(ast.Not(), not_expr(s))
    if s.accept(TokenType.LPAREN):
        ret = expr(s)
        s.accept(TokenType.RPAREN, reject=True)
        return ret
    ident = s.accept(TokenType.IDENT)
    if ident:
        return ast.Name(IDENT_PREFIX + ident.value, ast.Load())
    s.reject((TokenType.NOT, TokenType.LPAREN, TokenType.IDENT))


class MatcherAdapter(Mapping[str, bool]):
    """Adapts a matcher function to a locals mapping as required by eval()."""

    def __init__(self, matcher: Callable[[str], bool]) -> None:
        self.matcher = matcher

    def __getitem__(self, key: str) -> bool:
        return self.matcher(key[len(IDENT_PREFIX) :])

    def __iter__(self) -> Iterator[str]:
        raise NotImplementedError()

    def __len__(self) -> int:
        raise NotImplementedError()


class Expression:
    """A compiled match expression as used by -k and -m.

    The expression can be evaluated against different matchers.

    """

    __slots__ = ("code",)

    def __init__(self, code: types.CodeType) -> None:
        self.code = code

    @classmethod
    def compile_(cls, input_: str) -> Expression:
        """Compile a match expression.

        Parameters
        ----------
        input_: str
            The input expression - one line.

        """
        astexpr = expression(Scanner(input_))
        code: types.CodeType = compile(
            astexpr,
            filename="<pytask match expression>",
            mode="eval",
        )
        return cls(code)

    def evaluate(self, matcher: Callable[[str], bool]) -> bool:
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
        ret: bool = eval(self.code, {"__builtins__": {}}, MatcherAdapter(matcher))
        return ret

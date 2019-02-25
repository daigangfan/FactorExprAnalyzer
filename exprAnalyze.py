# lexer

tokens = [
    "ID", "NUMBER",
    "PLUS", "MINUS", "TIMES", "DIVIDE", "OR", "AND", "NOT",
    # "^" here
    "POWER",
    "LT", "LE", "GT", "GE", "EQ", "NE",
    "TERNARY",
    "LPAREN", "RPAREN",
    "COMMA", "COLON", "NEWLINE"
]

t_ID = r'[a-zA-Z_][a-zA-Z0-9_]*'
t_NUMBER = r"(\d+(\.\d*)?|\.\d+)"
t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE = r"/"
t_OR = r"\|"
t_AND = r"&"
t_NOT = r"!"
t_POWER = r"\^"
t_LT = r"<"
t_LE = r"<="
t_GT = r">"
t_GE = r">="
t_EQ = r"="
t_NE = r"!="
t_TERNARY = r"\?"
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_COMMA = r","
t_COLON = r":"
t_NEWLINE = r"\n"

t_ignore = ' \t'


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


# parser
import ast

import ply.lex as lex
import ply.yacc as yacc

binary_ops = {
    "+": ast.Add(),
    "-": ast.Sub(),
    "*": ast.Mult(),
    "/": ast.Div(),
    "<": ast.Lt(),
    ">": ast.Gt(),
    "=": ast.Eq(),
    "<=": ast.LtE(),
    ">=": ast.GtE(),
    "!=": ast.NotEq(),
    "^": ast.Pow(),
    "&": ast.And(),
    "|": ast.Or()

}
unary_ops = {
    "!": ast.Not(),
    "-": ast.USub()
}


def p_stmt(p):
    '''statement : test'''
    p[0] = ast.Expr(p[1])


def p_atom_name(p):
    '''atom : ID'''
    p[0] = ast.Name(id=p[1])


def p_atom_number(p):
    ''' atom : NUMBER '''
    p[0] = ast.Num(n=float(p[1]))


def p_trailer(p):
    ''' trailer : LPAREN arglist RPAREN'''
    p[0] = p[2]


def p_arglist(p):
    '''arglist : arglist COMMA argument 
               | argument'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]


def p_argument(p):
    ''' argument : test'''
    p[0] = p[1]


def p_atom_expr(p):
    ''' atom_expr : atom 
                  | atom trailer'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = ast.Call(func=p[1], args=p[2])


def p_power(p):
    '''power : atom_expr 
             | atom_expr POWER factor'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 4:
        p[0] = ast.BinOp(left=p[1], op=ast.Pow(), right=p[3])


def p_factor(p):
    '''
    factor : MINUS factor 
           | power
    '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = ast.UnaryOp(op=ast.USub(), operand=p[2])


def p_term(p):
    '''
    term : factor 
         | term TIMES factor 
         | term DIVIDE factor
    '''
    if len(p) == 2:
        p[0] = p[1]
    if len(p) == 4:
        p[0] = ast.BinOp(left=p[1], right=p[3], op=binary_ops[p[2]])


def p_arith_expr(p):
    '''
    arith_expr : term 
               | arith_expr PLUS term 
               | arith_expr MINUS term
    '''
    if len(p) == 2:
        p[0] = p[1]
    if len(p) == 4:
        p[0] = ast.BinOp(left=p[1], op=binary_ops[p[2]], right=p[3])


def p_comparison(p):
    '''
    comparison : arith_expr
                | comparison LT arith_expr
                | comparison GT arith_expr
                | comparison LE arith_expr
                | comparison GE arith_expr
                | comparison EQ arith_expr
                | comparison NE arith_expr
    '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 4:
        p[0] = ast.Compare(left=p[1], ops=[binary_ops[p[2]]], comparators=[p[3]])


def p_not_test(p):
    '''
    not_test : NOT not_test 
             | comparison
    '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = ast.UnaryOp(op=ast.Not(), operand=p[2])


def p_and_test(p):
    '''
    and_test : not_test 
             | and_test AND not_test
    '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 4:
        p[0] = ast.BoolOp(op=ast.And(), values=[p[1], p[3]])


def p_or_test(p):
    '''
    or_test : and_test 
            | or_test OR and_test
    '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 4:
        p[0] = ast.BoolOp(op=ast.Or(), values=[p[1], p[3]])


def p_test(p):
    '''
    test : or_test 
         | or_test TERNARY or_test COLON test
    '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 6:
        p[0] = ast.IfExp(test=p[1], body=p[3], orelse=p[5])


def p_atom_test(p):
    '''
    atom : LPAREN test RPAREN
    '''
    if len(p) == 4:
        p[0] = p[2]


lexer = lex.lex()

parser = yacc.yacc(start="statement")


def parse_expr(input):
    lexer.input(input)
    result = parser.parse(lexer=lexer, debug=True)
    print(ast.dump(result))
    return result


if __name__ == "__main__":
    parse_expr("a>b")

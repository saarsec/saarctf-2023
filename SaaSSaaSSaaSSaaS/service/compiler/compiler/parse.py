import ply.yacc as yacc

from .lex import tokens

from .ast_nodes import *

precedence = (
    ('nonassoc', 'EQUALS', 'GREATER'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('left', 'AND', 'OR', 'XOR'),
    ('right', 'UMINUS', 'NOT')
)


def p_prg_seq_topstmt(p):
    'prg : prg topstmt'
    p[0] = Sequence(p[1].stmts + [p[2]])


def p_prg_topstmt(p):
    'prg : topstmt'
    p[0] = Sequence([p[1]])


def p_topstmt_stmt(p):
    'topstmt : stmt'
    p[0] = p[1]


def p_top_stmt_funcdef(p):
    'topstmt : funcdef'
    p[0] = p[1]


def p_stmts_seq_stmt(p):
    'stmts : stmts stmt'
    p[0] = Sequence(p[1].stmts + [p[2]])


def p_stmts_stmt(p):
    'stmts : stmt'
    p[0] = Sequence([p[1]])


def p_funcdec(p):
    'funcdef : FUNCTION ID paramlist LBRACE stmts RBRACE EOL'
    p[0] = FuncDef(p[2], p[3], p[5])


def p_paramlist_seq(p):
    'paramlist : paramlist ARG ID SEP'
    p[0] = p[1] + [p[3]]


def p_paramlist_empty(p):
    'paramlist :'
    p[0] = []


# Statements
def p_stmt_assign(p):
    'stmt : ASSIGN ID expr EOL'
    p[0] = AssignStmt(p[2], p[3])


def p_stmt_if(p):
    'stmt : IF expr LBRACE stmts RBRACE EOL'
    p[0] = IfStmt(p[2], p[4])


def p_stmt_ret(p):
    'stmt : RETURN expr EOL'
    p[0] = Return(p[2])


def p_stmt_while(p):
    'stmt : WHILE expr LBRACE stmts RBRACE EOL'
    p[0] = WhileStmt(p[2], p[4])


def p_stmt_getchar(p):
    'stmt : GETCHAR ID EOL'
    p[0] = GetCharStmt(p[2])


def p_stmt_puts(p):
    'stmt : PUTS expr EOL'
    p[0] = PutsStmt(p[2])


def p_stmt_expr(p):
    'stmt : expr EOL'
    p[0] = ExprStmt(p[1])


def p_stmt_empty(p):
    'stmt : EOL'
    pass


def p_expr_call_noargs(p):
    'expr : CALL ID'
    p[0] = CallExpr(p[2], [])


# Expressions
def p_expr_call(p):
    'expr : arglist SEP CALL ID'
    p[0] = CallExpr(p[4], p[1])


def p_arglist_expr(p):
    'arglist : arglist SEP ARG expr'
    p[0] = p[1] + [p[4]]


def p_arglist_single(p):
    'arglist : ARG expr'
    p[0] = [p[2]]


def p_expr_equals(p):
    'expr : expr EQUALS expr'
    p[0] = BinaryExpr(p[1], '=', p[3])


def p_expr_greater(p):
    'expr : expr GREATER expr'
    p[0] = BinaryExpr(p[1], '>', p[3])


def p_expr_plus(p):
    'expr : expr PLUS expr'
    p[0] = BinaryExpr(p[1], '+', p[3])


def p_expr_minus(p):
    'expr : expr MINUS expr'
    p[0] = BinaryExpr(p[1], '-', p[3])


def p_expr_times(p):
    'expr : expr TIMES expr'
    p[0] = BinaryExpr(p[1], '*', p[3])


def p_expr_divide(p):
    'expr : expr DIVIDE expr'
    p[0] = BinaryExpr(p[1], '/', p[3])


def p_expr_and(p):
    'expr : expr AND expr'
    p[0] = BinaryExpr(p[1], '&', p[3])


def p_expr_or(p):
    'expr : expr OR expr'
    p[0] = BinaryExpr(p[1], '|', p[3])


def p_expr_xor(p):
    'expr : expr XOR expr'
    p[0] = BinaryExpr(p[1], '^', p[3])


def p_expr_uminus(p):
    'expr : MINUS expr %prec UMINUS'
    p[0] = UnaryExpr(p[2], '-')


def p_expr_not(p):
    'expr : NOT expr'
    p[0] = UnaryExpr(p[2], '!')


def p_expr_expr(p):
    'expr : LPAREN expr RPAREN'
    p[0] = p[2]


def p_expr_number(p):
    'expr : NUMBER'
    p[0] = IntLiteral(p[1])


def p_expr_string(p):
    'expr : STRING'
    p[0] = StringLiteral(p[1])


def p_expr_id(p):
    'expr : ID'
    p[0] = VarRead(p[1])


# Error rule for syntax errors
def p_error(p):
    print(f"Syntax error at {p}")


parser = yacc.yacc(debug=True)

import ply.lex as lex

tokens = (
    'NUMBER',
    'STRING',
    'ID',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'AND',
    'OR',
    'XOR',
    'EQUALS',
    'GREATER',
    'NOT',
    'ASSIGN',
    'LPAREN',
    'RPAREN',
    'LBRACE',
    'RBRACE',
    'WHILE',
    'IF',
    'ARG',
    'SEP',
    'FUNCTION',
    'RETURN',
    'CALL',
    'PUTS',
    'GETCHAR',
    'EOL'
)

# Regular expression rules for simple tokens
t_ASSIGN = r'[Mm]ach'
t_PLUS = r'[Bb]abbe\ an'
t_MINUS = r'[Nn]imm\ [Ff]ord'
t_TIMES = r'[Mm]ohl'
t_DIVIDE = r'[Ii]n\ [Ss]tiggsche'
t_AND = r'[Uu]nn'
t_OR = r'[Oo]dder'
t_XOR = r'[Vv]erkrumbele'
t_GREATER = r'[Ii]ss?\ [Bb]esser\ [Aa]ls'
t_EQUALS = r'[Ii]ss?'
t_NOT = r'[Nn]idd'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'[Mm]ach\ [Aa]llemohl'
t_RBRACE = r'[Aa]weil\ [Ii]ss?\ [Aa]wwer\ [Ss]chluss'
t_WHILE = r'[Ss]o\ ?[Ll]ang'
t_IF = r'[Ww]enn'
t_ARG = r'[Hh]olle'
t_SEP = r'[Uu]nn\ [Dd]ann'
t_FUNCTION = r'[Vv]ergliggere'
t_RETURN = r'[Tt]appe\ [Hh]emm\ [Uu]nn\ [Hh]olle'
t_CALL = r'[Gg]eh\ [Uu]ff\ [Tt]rulla\ [Bb]ei'
t_PUTS = r'[Bb]rundse'
t_GETCHAR = r'[Ss]chnäge'


# Functions for complex tokens
@lex.TOKEN(r'\d+')
def t_NUMBER(t):
    t.value = int(t.value)
    return t


@lex.TOKEN(r'"([^"\n]|(\\"))*"')
def t_STRING(t):
    t.value = t.value[1:-1].replace("\\\"", "\"")
    return t


@lex.TOKEN(r'(\'s|ähs)\ ([A-ZÄÖÜ][a-zäöü]*)')
def t_ID(t):
    t.value = t.value.split()[-1]
    return t


# Ingore whitespace
t_ignore = ' \t'

# Ignore comments starting with '#'
t_ignore_COMMENT = r'\#.*'


# Ignore line-endings, but count number of lines
@lex.TOKEN(r'[.!\n\r]+')
def t_EOL(t):
    t.lexer.lineno += t.value.count('\n')
    return t


# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


lexer = lex.lex()

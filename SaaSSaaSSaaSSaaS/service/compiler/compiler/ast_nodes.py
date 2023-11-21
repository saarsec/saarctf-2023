class Expr:
    def accept(self, visitor):
        return getattr(visitor, f"visit_{self.__class__.__name__}")(self)


class IntLiteral(Expr):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'Int({self.value})'


class StringLiteral(Expr):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'Str({self.value})'


class VarRead(Expr):
    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return f'Var({self.id})'


class UnaryExpr(Expr):
    def __init__(self, expr, op):
        self.expr = expr
        self.op = op

    def __repr__(self):
        return f'({self.op} {repr(self.expr)})'


class BinaryExpr(Expr):
    def __init__(self, lhs, op, rhs):
        self.lhs = lhs
        self.op = op
        self.rhs = rhs

    def __repr__(self):
        return f'({self.op} {repr(self.lhs)} {repr(self.rhs)})'


class CallExpr(Expr):
    def __init__(self, funcid, args):
        self.funcid = funcid
        self.args = args

    def __repr__(self):
        return f'(call {self.funcid} ' + ','.join(repr(a) for a in self.args) + ')'


class Stmt:
    def accept(self, visitor):
        return getattr(visitor, f"visit_{self.__class__.__name__}")(self)


class Sequence(Stmt):
    def __init__(self, stmts):
        self.stmts = [s for s in stmts if s is not None]

    def __repr__(self):
        return '(' + ';'.join(repr(s) for s in self.stmts) + ')'


class AssignStmt(Stmt):
    def __init__(self, id, expr):
        self.id = id
        self.expr = expr

    def __repr__(self):
        return f'(assign {self.id} {repr(self.expr)}'


class IfStmt(Stmt):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

    def __repr__(self):
        return f'(if {repr(self.condition)} {repr(self.body)})'


class WhileStmt(Stmt):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

    def __repr__(self):
        return f'(while {repr(self.condition)} {repr(self.body)})'


class FuncDef(Stmt):
    def __init__(self, id, params, body):
        self.id = id
        self.params = params
        self.body = body

    def __repr__(self):
        return f'(def {self.id} {repr(self.params)} {repr(self.body)})'


class Return(Stmt):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f'(return {repr(self.expr)})'


class ExprStmt(Stmt):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return repr(self.expr)


class GetCharStmt(Stmt):
    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return f'(read {self.id})'


class PutsStmt(Stmt):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f'(puts {self.expr})'

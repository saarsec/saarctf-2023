class PrinterError(ValueError):
    pass


class Formatter:

    def _indent(self, x):
        return '\n'.join('  ' + l for l in x.splitlines())

    def format(self, n):
        return n.accept(self)

    def visit_IntLiteral(self, n):
        return f"{n.value}"

    def visit_StringLiteral(self, n):
        return f"\"{n.value}\""

    def visit_VarRead(self, n):
        return f"'s {n.id}"

    def visit_UnaryExpr(self, n):
        if n.op == '!':
            return f"(nidd {n.expr.accept(self)})"
        else:
            raise PrinterError(f"Unknown unary operand {n.op}")

    def visit_BinaryExpr(self, n):
        OPERANDS = {
            '=': 'iss',
            '>': 'iss besser als',
            '+': 'babbe an',
            '-': 'nimm ford',
            '*': 'mohl',
            '/': 'in Stiggsche'
        }
        if n.op not in OPERANDS:
            raise PrinterError(f"Unknown binary operand {n.op}")
        return f"({n.lhs.accept(self)} {OPERANDS[n.op]} {n.rhs.accept(self)})"

    def visit_CallExpr(self, n):
        arglist = ""
        if n.args:
            arglist = ''.join(f"holle {a.accept(self)} unn dann " for a in n.args)
        return f"{arglist}geh uff Trulla bei 's {n.funcid}"

    def visit_Sequence(self, n):
        return ''.join(f"{s.accept(self)}\n" for s in n.stmts)

    def visit_AssignStmt(self, n):
        return f"Mach 's {n.id} {n.expr.accept(self)}"

    def visit_IfStmt(self, n):
        ret = f'Wenn {n.condition.accept(self)} mach allemohl\n'
        ret += f"{self._indent(n.body.accept(self))}\n"
        ret += 'Aweil is awwer Schluss!'
        return ret

    def visit_WhileStmt(self, n):
        ret = f'Solang {n.condition.accept(self)} mach allemohl\n'
        ret += f"{self._indent(n.body.accept(self))}\n"
        ret += 'Aweil is awwer Schluss!'
        return ret

    def visit_FuncDef(self, n):
        paramlist = ""
        if n.params:
            paramlist = ''.join(f"holle 's {p} unn dann " for p in n.params)
        ret = f"Vergliggere 's {n.id} {paramlist} mach allemohl\n"
        ret += f"{self._indent(n.body.accept(self))}\n"
        ret += 'Aweil is awwer Schluss!'
        return ret

    def visit_Return(self, n):
        return f"Tappe Hemm unn holle {n.expr.accept(self)}"

    def visit_ExprStmt(self, n):
        return n.expr.accept(self)

    def visit_GetCharStmt(self, n):
        return f"Schnäge 's {n.id}"

    def visit_PutsStmt(self, n):
        return f"Brundse {n.expr.accept(self)}"

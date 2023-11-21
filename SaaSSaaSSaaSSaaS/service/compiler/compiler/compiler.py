class CompileError(ValueError):
    pass


# opcode, stackdelta
OP_PUSH_INT = (0x01, 1)
OP_PUSH_STR = (0x02, 1)
OP_ADD = (0x10, -1)
OP_SUB = (0x11, -1)
OP_MUL = (0x12, -1)
OP_DIV = (0x13, -1)
OP_AND = (0x14, -1)
OP_OR = (0x15, -1)
OP_XOR = (0x16, -1)
OP_NOT = (0x17, 0)
OP_EQ = (0x20, -1)
OP_LT = (0x21, -1)
OP_DUP = (0x30, 0)
OP_SWAP = (0x31, -1)
OP_POP = (0x32, -1)
OP_JMP = (0x40, -1)
OP_JMPI = (0x41, -2)
OP_SYSCALL = (0x42, -1)  # + arguments

MAGIC = b'SAAR'


class Compiler:

    def __init__(self):
        self.stack_depth = 0
        self.scope = {}  # dict of local variable-locations
        self.labels = dict()  # mapping from label to location
        self.relocs = dict()  # mapping from location to pointed-to label
        self.code = bytearray()

    def _fix_relocs(self):
        for loc, label in self.relocs.items():
            if label not in self.labels or self.labels[label] is None:
                raise CompileError(f"Error, label {label} is not defined")
            self.code[loc:loc + 2] = self.labels[label].to_bytes(2, 'little')

    def _add(self, op):
        opcode, stack_delta = op
        self.code.append(opcode)
        self.stack_depth += stack_delta

    def _new_label(self, prefix):
        new_label = f"{prefix}_{len(self.labels)}"
        self.labels[new_label] = None
        return new_label

    def _push_int(self, value):
        self._add(OP_PUSH_INT)
        self.code += value.to_bytes(2, 'little')

    def _push_ref(self, label):
        self._add(OP_PUSH_INT)
        self.relocs[len(self.code)] = label
        self.code += b'\x00\x00'

    def _push_str(self, string):
        encoded = string.encode()
        self._add(OP_PUSH_STR)
        self.code += len(encoded).to_bytes(2, 'little')
        self.code += encoded

    def _set_label(self, label):
        self.labels[label] = len(self.code)

    def _get_var_loc(self, id):
        return self.stack_depth - self.scope[id]

    def _set_var_loc(self, id):
        self.scope[id] = self.stack_depth

    def compile(self, n):
        n.accept(self)
        self._fix_relocs()
        return bytes(MAGIC + self.code)

    def visit_IntLiteral(self, n):
        self._push_int(n.value)

    def visit_StringLiteral(self, n):
        self._push_str(n.value)

    def visit_VarRead(self, n):
        if n.id not in self.scope:
            raise CompileError(f"Error, variable {n.id} not defined in current scope")
        relative_location = self._get_var_loc(n.id)
        self._push_int(relative_location)
        self._add(OP_DUP)

    def visit_UnaryExpr(self, n):
        OPS = {
            '!': OP_NOT
        }
        if n.op not in OPS:
            raise CompileError(f"Unknown unary operand {n.op}")
        self._add(OPS[n.op])

    def visit_BinaryExpr(self, n):
        OPS = {
            '=': OP_EQ,
            '>': OP_LT,
            '+': OP_ADD,
            '-': OP_SUB,
            '*': OP_MUL,
            '/': OP_DIV,
            '^': OP_XOR,
            '|': OP_OR,
            '&': OP_AND,
        }
        if n.op not in OPS:
            raise CompileError(f"Unknown binary operand {n.op}")
        op = OPS[n.op]
        if op == OP_LT:
            n.rhs.accept(self)
            n.lhs.accept(self)
        else:
            n.lhs.accept(self)
            n.rhs.accept(self)
        self._add(op)

    def visit_CallExpr(self, n):
        # 1. Push return address
        ret_label = self._new_label('_ret')
        self._push_ref(ret_label)
        # 2. Push all arguments
        for arg in n.args:
            arg.accept(self)
        # 3. Push function address
        self._push_ref(n.funcid)
        # 4. Do the call
        self._add(OP_JMP)
        # 5. Adjust stack-depth
        self.stack_depth -= len(n.args) + 1 - 1  # arguments + return-address - return-value
        # 6. Set return-label location
        self._set_label(ret_label)

    def visit_Sequence(self, n):
        for stmt in n.stmts:
            stmt.accept(self)

    def visit_AssignStmt(self, n):
        n.expr.accept(self)
        if n.id in self.scope:
            relative_location = self._get_var_loc(n.id)
            self._push_int(relative_location)
            self._add(OP_SWAP)
            self._add(OP_POP)
        else:
            self._set_var_loc(n.id)

    def visit_IfStmt(self, n):
        # 0. Record old scope and stack-depth
        scope = self.scope
        stack_depth = self.stack_depth
        # 1. Push else-label
        jmp_label = self._new_label('_if')
        self._push_ref(jmp_label)
        # 2. Evaluate condition
        n.condition.accept(self)
        # 3. Invert condition for indirect jump
        self._add(OP_NOT)
        # 4. Perform conditional jump over body
        self._add(OP_JMPI)
        # 5. Compile body
        n.body.accept(self)
        # 6. Adjust stack-depth if necessary
        while self.stack_depth > stack_depth:
            self._add(OP_POP)
        self.stack_depth = stack_depth
        self.scope = scope
        # 7. Place else-label
        self._set_label(jmp_label)

    def visit_WhileStmt(self, n):
        # 0. Record old scope and stack-depth
        scope = self.scope
        stack_depth = self.stack_depth
        # 1. Place loop-label
        loop_label = self._new_label('_while_loop')
        self._set_label(loop_label)
        # 2. Push after-label
        jmp_label = self._new_label('_while_end')
        self._push_ref(jmp_label)
        # 3. Evaluate condition
        n.condition.accept(self)
        # 4. Invert condition for indirect jump
        self._add(OP_NOT)
        # 5. Perform conditional jump over body
        self._add(OP_JMPI)
        # 6. Compile body
        n.body.accept(self)
        # 7. Adjust stack-depth if necessary
        while self.stack_depth > stack_depth:
            self._add(OP_POP)
        self.stack_depth = stack_depth
        self.scope = scope
        # 8. Jump to begin of loop
        self._push_ref(loop_label)
        self._add(OP_JMP)
        # 9. Place else-label
        self._set_label(jmp_label)

    def visit_FuncDef(self, n):
        # 0. Record old scope and stack-depth
        scope = self.scope
        stack_depth = self.stack_depth
        # 1. Jump over function in regular control-flow
        jmp_label = self._new_label('_func')
        self._push_ref(jmp_label)
        self._add(OP_JMP)
        # 2. Place function label
        self._set_label(n.id)
        # 3. Create new scope for function
        self.scope = {'_RET': 1} | {p: i for i, p in enumerate(n.params, 2)}
        self.stack_depth = len(self.scope)
        # 4. Compile function body
        n.body.accept(self)
        # 5. Leave scope
        self.scope = scope
        self.stack_depth = stack_depth
        # 6. Place jump-label
        self._set_label(jmp_label)

    def visit_Return(self, n):
        # 1. Evaluate expression
        n.expr.accept(self)
        # Stack-layout now: OLD_STACK, RETADDR, ARG1, ARG2, ARG3, RETVAL
        # 2. Swap with return-address
        ret_loc = self._get_var_loc('_RET')
        self._push_int(ret_loc)
        self._add(OP_SWAP)
        # Stack-layout now: OLD_STACK, RETVAL, ARG1, ARG2, ARG3, RETADDR
        # 3. Swap with slot just above return-address
        self._push_int(ret_loc - 1)
        self._add(OP_SWAP)
        # Stack-layout now: OLD_STACK, RETVAL, RETADDR, ARG2, ARG3, ARG1
        # 4. Pop everything except return value and address
        while self.stack_depth > 2:
            self._add(OP_POP)
        # Stack-layout now: OLD_STACK, RETVAL, RETADDR
        # 5. Perform the jump
        self._add(OP_JMP)

    def visit_ExprStmt(self, n):
        n.expr.accept(self)
        self._add(OP_POP)

    def visit_GetCharStmt(self, n):
        self._push_int(0)
        self._push_str('getchar')
        self._add(OP_SYSCALL)
        if n.id in self.scope:
            relative_location = self._get_var_loc(n.id)
            self._push_int(relative_location)
            self._add(OP_SWAP)
            self._add(OP_POP)
        else:
            self._set_var_loc(n.id)

    def visit_PutsStmt(self, n):
        n.expr.accept(self)
        self._push_int(1)
        self._push_str('puts')
        self._add(OP_SYSCALL)
        self._add(OP_POP)
        self.stack_depth -= 1  # one argument was read

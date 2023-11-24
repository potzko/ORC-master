import orc_parser

class ir:
    def __init__(self, fn_names) -> None:
        self.tmp_count = 0
        self.lable_count = -1
        self.Mov = self._construct('mov', 2)
        self.Lea = self._construct('lea', 3)
        self.Add = self._construct('add', 3)
        self.Mul = self._construct('mul', 3)
        self.Div = self._construct('div', 3)
        self.Mod = self._construct('mod', 3)
        self.And = self._construct('and', 3)
        self.Or = self._construct('or', 3)
        self.Xor = self._construct('xor', 3)
        self.Fcall = self._construct("fcall", 3)
        self.Neg = self._construct("neg", 2)
        self.Not = self._construct("not", 2)
        self.Copy = self._construct("copy", 2)
        self.Read = self._construct("read", 2)
        self.Write = self._construct("write", 2) 
        self.Neq = self._construct("neq", 3)
        self.Eq = self._construct("eq", 3)
        self.Ifnz = self._construct("ifnz", 2)
        self.Ret = self._construct("ret", 1)
        self.Jmp = self._construct("jmp", 1)
        self.Nop = self._construct("nop", 0)
        self.Lt = self._construct("lt", 3)
        self.Le = self._construct("le", 3)
        self.EndP = self._construct("endp", 1)
        self.Proc = self._construct("proc", 1)

        print(fn_names)
        names = [i[0][1] for i in fn_names]
        args  = [[ii[1] for ii in i[1]] for i in fn_names]
        print(names)
        print(args)
        
        self.fn_table = {i[0][1]: (f"{i[0][1]}", {ii[1]: f"@F{ind_ii}" for ind_ii, ii in enumerate(i[1])}) for ind, i in enumerate(fn_names)}

    def create_tmp(self):
        self.tmp_count += 1
        return f"@{self.tmp_count}"
    
    def create_lable(self):
        self.lable_count += 1
        return f"L@{self.lable_count}"
    
    def _construct(self, st, val_count):
        ret_str = f'{st} ' + ' {}'*val_count + '\n'
        def ret(*args):
            if len(args) != val_count:
                raise Exception(f'expected {val_count} variables, found {len(args)} instead')
            return ret_str.format(*args)
        return ret

    def lable(self, l):
        return l + '\n'

    def function_list(self, node):
        ret = ""
        for i in node[1:]:
            ret += self.function(i)
        return ret

    def function(self, node):
        scope = self.fn_table[node[1][1]][1]
        ret = ''
        ret += self.Proc(self.fn_table[node[1][1]][0])
        ret += self.statement(node[3], scope)
        ret += self.Ret("@0")
        ret += self.EndP(self.fn_table[node[1][1]][0])
        return ret

    def statement(self, node, scope):
        if not node:
            return self.Nop()
        
        primary, *secondary = node
        ret = ''
        #print("primery: ", primary, "\nsecondary: ", secondary)
        match primary:
            case 'let':
                scope[secondary[0][1]] = self.create_tmp()
                ret += self.expression(scope[secondary[0][1]], secondary[1], scope)
            case "statement_list":
                nested_scope = scope.copy()
                for i in secondary:
                    ret += self.statement(i, nested_scope)
            case "if":
                cond = self.create_tmp()
                cond_eval = self.expression(cond, node[1], scope)
                state_true = self.statement(node[2], scope.copy())
                state_false = self.statement(node[3], scope.copy())
                block_true = self.create_lable()
                block_end = self.create_lable()

                ret += cond_eval
                ret += self.Ifnz(cond, block_true)
                ret += state_false
                ret += self.Jmp(block_end)
                ret += self.lable(block_true)
                ret += state_true
                ret += self.lable(block_end)
            case "while":
                cond = self.create_tmp()
                cond_eval = self.expression(cond, node[1], scope)
                state_true = self.statement(node[2], scope.copy())
                block_loop = self.create_lable()
                block_loop_start = self.create_lable()
                block_end = self.create_lable()

                ret += self.lable(block_loop)
                ret += cond_eval
                ret += self.Ifnz(cond, block_loop_start)
                ret += self.Jmp(block_end)
                ret += self.lable(block_loop_start)
                ret += state_true
                ret += self.Jmp(block_loop)
                ret += self.lable(block_end)
            case "return":
                tmp = self.create_tmp()
                ret += self.expression(tmp, secondary[0], scope)
                ret += self.Ret(tmp)

            case  _:
                ret += self.expression(self.create_tmp() ,node, scope)
        return ret
    

    def expression(self, output_reg, exp, scope) -> None:
        if len(exp) == 0:
            return self.Nop()
        ret = ''
        match exp[0]:
            #single expressions
            case 'identifier':
                ret += self.Lea(output_reg, scope[exp[1]], 0)
            case 'literal_num':
                ret += self.Mov(output_reg, exp[1])
            #binary expressions
            case '=':
                tmp = self.create_tmp()
                ret += self.expression(tmp, exp[2], scope)
                ret += self.Mov(scope[exp[1][1]], tmp)
            case '+':
                tmp1 , tmp2 = self.create_tmp(), self.create_tmp()
                ret += self.expression(tmp1, exp[1], scope)
                ret += self.expression(tmp2, exp[2], scope)
                ret += self.Add(output_reg, tmp1, tmp2)
            case '-':
                tmp1 , tmp2 = self.create_tmp(), self.create_tmp()
                ret += self.expression(tmp1, exp[1], scope)
                ret += self.expression(tmp2, exp[2], scope)
                ret += self.Neg(tmp2, tmp2)
                ret += self.Add(output_reg, tmp1, tmp2)
            case '*':
                tmp1 , tmp2 = self.create_tmp(), self.create_tmp()
                ret += self.expression(tmp1, exp[1], scope)
                ret += self.expression(tmp2, exp[2], scope)
                ret += self.Mul(output_reg, tmp1, tmp2)
            case '/':
                tmp1 , tmp2 = self.create_tmp(), self.create_tmp()
                ret += self.expression(tmp1, exp[1], scope)
                ret += self.expression(tmp2, exp[2], scope)
                ret += self.Div(output_reg, tmp1, tmp2)
            case '%':
                tmp1 , tmp2 = self.create_tmp(), self.create_tmp()
                ret += self.expression(tmp1, exp[1], scope)
                ret += self.expression(tmp2, exp[2], scope)
                ret += self.Mod(output_reg, tmp1, tmp2)
            case '^':
                tmp1 , tmp2 = self.create_tmp(), self.create_tmp()
                ret += self.expression(tmp1, exp[1], scope)
                ret += self.expression(tmp2, exp[2], scope)
                ret += self.Xor(output_reg, tmp1, tmp2)
            case '&&':
                tmp1 , tmp2 = self.create_tmp(), self.create_tmp()
                ret += self.expression(tmp1, exp[1], scope)
                ret += self.expression(tmp2, exp[2], scope)
                ret += self.And(output_reg, tmp1, tmp2)
            case '||':
                tmp1 , tmp2 = self.create_tmp(), self.create_tmp()
                ret += self.expression(tmp1, exp[1], scope)
                ret += self.expression(tmp2, exp[2], scope)
                ret += self.Or(output_reg, tmp1, tmp2)
            case '==':
                tmp1 , tmp2 = self.create_tmp(), self.create_tmp()
                ret += self.expression(tmp1, exp[1], scope)
                ret += self.expression(tmp2, exp[2], scope)
                ret += self.Eq(output_reg, tmp1, tmp2)
            case '<':
                tmp1 , tmp2 = self.create_tmp(), self.create_tmp()
                ret += self.expression(tmp1, exp[1], scope)
                ret += self.expression(tmp2, exp[2], scope)
                ret += self.Lt(output_reg, tmp1, tmp2)
            case '>':
                tmp1 , tmp2 = self.create_tmp(), self.create_tmp()
                ret += self.expression(tmp2, exp[1], scope)
                ret += self.expression(tmp1, exp[2], scope)
                ret += self.Lt(output_reg, tmp1, tmp2)
            case '<=':
                tmp1 , tmp2 = self.create_tmp(), self.create_tmp()
                ret += self.expression(tmp1, exp[1], scope)
                ret += self.expression(tmp2, exp[2], scope)
                ret += self.Le(output_reg, tmp1, tmp2)
            case '>=':
                tmp1 , tmp2 = self.create_tmp(), self.create_tmp()
                ret += self.expression(tmp2, exp[1], scope)
                ret += self.expression(tmp1, exp[2], scope)
                ret += self.Lt(output_reg, tmp1, tmp2)
            case '!=':
                tmp1 , tmp2 = self.create_tmp(), self.create_tmp()
                ret += self.expression(tmp1, exp[1], scope)
                ret += self.expression(tmp2, exp[2], scope)
                ret += self.Neq(output_reg, tmp1, tmp2)
            
            #unary expressions
            case "unary_op":
                match exp[1]:
                    case '+': ret += self.Nop()
                    case '-': ret += self.expression(output_reg, exp[2], scope) + self.Neg(output_reg, output_reg)
                    case '&': ret += self.expression(output_reg, exp[2], scope) + self.Read(output_reg, output_reg)
                    case '!': ret += self.expression(output_reg, exp[2], scope) + self.Not(output_reg, output_reg)
                    case _: raise Exception(f'oh nyo :3')
            
            case 'call':
                args = [self.create_tmp() for i in range(len(exp[2]) - 1)]
                for a, b in zip(args, exp[2][1:]):
                    ret += self.expression(a, b, scope)
                ret += self.Fcall(output_reg, self.fn_table[exp[1]][0], " ".join(args))

            case _:
                raise Exception(f'oh nyo')
    #\+|-|&|\!
        return ret

def format_code(ir_code):
    lines = ir_code.split('\n')
    ret = ''
    for i in lines:
        toks = i.split(' ')
        for i in toks:
            ret += i + ' '*(7 - len(i))
        ret += '\n'
    return ret



def compile(code):
    program, names = orc_parser.parser(code).program()
    ir_compiler = ir(names)
    ret = ir_compiler.function_list(program)
    return ret

    
if __name__ == '__main__':
    code = """
fn fibo x: {
    if (x < 2)
        return x;
    return fibo(x - 1) + fibo(x - 2);
}
fn main: {
    fibo(20);
}
"""
    print(compile(code))
import orc_parser

code = """
fn pow a, b: {
    print(a, b);
    if b == 0 {
        return 1;
    } else {
        let tmp: u64 = pow(a, b / 2);
        let a_tmp: u64 = 1;
        if b % 2 == 1 a_tmp = a;
        return a_tmp * tmp * tmp;
    }
}

fn factor num: {
    let i: u8 = 2;
    while 2 <= num {
        while num % i == 0 {
            //print(i);
            num = num / i;
        }
        i = i + 1;
    }
}

fn main: {
    return (pow(2, 63) - 1) * 2 + 1;
}
"""

parser = orc_parser.parser(code)
program, functions = parser.program()
#print(functions)

class interpreter:
    def __init__(self, functions, node) -> None:
        self.func = {i[0][1]: [ii[1] for ii in i[1]] for i in functions}
        self.func_lookup = {i[1][1]: i[3] for i in node[1:]}
        self.inbuilt = {'print': print}
        self.type_lookup = {f'u{i}': construct_integer_type(i) for i in [8, 16, 32, 64]}
        print(self.type_lookup)

    def _get_num(self, num, type = 'u8'):
        return self.expression(('literal_num', num, type), {})

    def function(self, name, values):
        if name in self.inbuilt:
            return self.inbuilt[name](*values)
        if not name in self.func:
            raise Exception(f"function {name}, not found")
        node = self.func_lookup[name]
        signature = self.func[name]
        if len(values) != len(signature):
            raise Exception(f"function {name} got {len(values)} arguments, expected {len(signature)}")
        scope = {name: value for name, value in zip(signature, values)}
        return self.statement(node, scope)
    
    def statement(self, node, scope):
        print(node)
        if len(node) == 0:
            return
        primary, *secondary = node
        match primary:
            case 'let':
                name, value, type = secondary[0], secondary[1], secondary[2]
                if name in scope:
                    raise Exception("not supported")
                scope[name[1]] = self.type_lookup[type](self.expression(value, scope))
            case '=':
                scope[secondary[0][1]] = self.expression(secondary[1], scope)
            case 'return':
                return self.expression(secondary[0], scope)
            case 'if':
                if self.expression(secondary[0], scope) != self._get_num(0):
                    return self.statement(secondary[1], scope)
                else:
                    return self.statement(secondary[2], scope)
            case 'statement_list':
                for i in secondary:
                    ret = self.statement(i, scope)
                    if ret is not None:
                        return ret
            case 'while':
                cond = self.expression(secondary[0], scope)
                while cond != self._get_num(0):
                    ret = self.statement(secondary[1], scope)
                    if ret != None:
                        return ret
                    cond = self.expression(secondary[0], scope)
            case _:
                self.expression(node, scope)
    
    def expression(self, exp, scope):
        print(exp)
        match exp[0]:
            case 'literal_num':
                return self.type_lookup[exp[2]](int(exp[1]))
            case 'literal_string':
                return exp[1]
            case 'identifier':
                return scope[exp[1]]
            case '+':
                return self.expression(exp[1], scope) + self.expression(exp[2], scope)
            case '-':
                return self.expression(exp[1], scope) - self.expression(exp[2], scope)
            case '%':
                return self.expression(exp[1], scope) % self.expression(exp[2], scope)
            case '/':
                return self.expression(exp[1], scope) // self.expression(exp[2], scope)
            case '*':
                return self.expression(exp[1], scope) * self.expression(exp[2], scope)
            case '<':
                return self._get_num(1) if self.expression(exp[1], scope) < self.expression(exp[2], scope) else self._get_num(0)
            case '<=':
                return self._get_num(1) if self.expression(exp[1], scope) <= self.expression(exp[2], scope) else self._get_num(0)
            case '==':
                return self._get_num(1) if self.expression(exp[1], scope) == self.expression(exp[2], scope) else self._get_num(0)
            case 'call':
                return self.function(exp[1], [self.expression(i, scope) for i in exp[2][1:]])
            case _:
                raise Exception(f"expression error, {exp[0]} not supported")


def construct_integer_type(byte_count):
    class ret:
        def __init__(self, value) -> None:
            print('init', value)
            if type(value) != int:
                value = value.value
            self.size = byte_count
            self.value = value % (2 ** byte_count)
        
        def __eq__(self, other) -> bool:
            return self.value == other.value
        def __add__(self, other):
            if self.size < other.size:
                return other + self
            return ret(self.value + other.value)
        def __sub__(self, other):
            if self.size < other.size:
                return other - self
            return ret(self.value - other.value)
        def __mul__(self, other):
            if self.size < other.size:
                return other * self
            return ret(self.value * other.value)
        def __floordiv__(self, other):
            if self.size < other.size:
                return other // self
            return ret(self.value // other.value)
        def __mod__(self, other):
            if self.size < other.size:
                return other % self
            return ret(self.value % other.value)
        def __str__(self) -> str:
            return f'{self.value}: u{self.size}'
    return ret
        
        
inter = interpreter(functions, program)
print(inter.function('main', []))
import IR_compiler
code = """
fn fibo x: {
    if x < 2 return x;
    return fibo(x - 1) + fibo(x - 2);
}
"""
ir_code = IR_compiler.compile(code)
print(ir_code)

class compiler:
    def __init__(self) -> None:
        pass

    def _construct(self, st, val_count):
        ret_str = f'{st} ' + ' {}'*val_count + '\n'
        def ret(*args):
            if len(args) != val_count:
                raise Exception(f'expected {val_count} variables, found {len(args)} instead')
            return ret_str.format(*args)
        return ret
class Token:
    def __init__(self, type, value=None):
        self.type = type  # Token type
        self.value = value  # Token value

    def __str__(self):
        return f'Token({self.type}, {repr(self.value)})'

    def __repr__(self):
        return self.__str__()

class Lexer:
    def __init__(self, text):
        self.text = text.replace('\r', '')  # Remove carriage returns
        self.pos = 0
        self.current_char = self.text[self.pos] if self.text else None

    def advance(self):
        """Advance the 'pos' pointer and set 'current_char'."""
        self.pos += 1
        if self.pos >= len(self.text):
            self.current_char = None  # Indicates end of input
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        """Skip any whitespace characters."""
        while self.current_char is not None and self.current_char in ' \t\n':
            self.advance()

    def get_next_token(self):
        """Lexical analyzer (tokenizer)"""
        while self.current_char is not None:
            if self.current_char in ' \t\n':
                self.skip_whitespace()
                continue

            if self.current_char in '=G+-*/%PIW{}#<':
                char = self.current_char
                self.advance()
                return Token(char)

            if self.current_char.islower():
                var = self.current_char
                self.advance()
                return Token('VARIABLE', var)

            if self.current_char.isdigit():
                num = self.current_char
                self.advance()
                return Token('NUMBER', num)

            # Unrecognized character
            raise Exception(f'Invalid character: {self.current_char}')

        return Token('EOF')

class ASTNode:
    def generate_code(self, code_generator):
        raise NotImplementedError

class ProgramNode(ASTNode):
    def __init__(self, commands):
        self.commands = commands

    def generate_code(self, code_generator):
        for cmd in self.commands:
            cmd.generate_code(code_generator)

class AssignCommandNode(ASTNode):
    def __init__(self, var, value):
        self.var = var
        self.value = value

    def generate_code(self, code_generator):
        code_generator.add_variable(self.var)
        val_code = self.value.generate_code(code_generator)
        code_generator.emit(f'{code_generator.indent()}{self.var} = {val_code};')

class GetCommandNode(ASTNode):
    def __init__(self, var):
        self.var = var

    def generate_code(self, code_generator):
        code_generator.add_variable(self.var)
        code_generator.emit(f'{code_generator.indent()}{{ gets(str);')
        code_generator.emit(f'{code_generator.indent()}sscanf(str, "%d", &{self.var});')
        code_generator.emit(f'{code_generator.indent()}}}')

class BinaryOperationNode(ASTNode):
    def __init__(self, operator, var, left, right):
        self.operator = operator
        self.var = var
        self.left = left
        self.right = right

    def generate_code(self, code_generator):
        code_generator.add_variable(self.var)
        left_code = self.left.generate_code(code_generator)
        right_code = self.right.generate_code(code_generator)
        code_generator.emit(f'{code_generator.indent()}{self.var} = {left_code} {self.operator} {right_code};')

class PrintCommandNode(ASTNode):
    def __init__(self, value):
        self.value = value

    def generate_code(self, code_generator):
        val_code = self.value.generate_code(code_generator)
        code_generator.emit(f'{code_generator.indent()}printf("%d\\n", {val_code});')

class IfCommandNode(ASTNode):
    def __init__(self, comparison, command):
        self.comparison = comparison
        self.command = command

    def generate_code(self, code_generator):
        comp_code = self.comparison.generate_code(code_generator)
        code_generator.emit(f'{code_generator.indent()}if ( {comp_code} ) {{')
        code_generator.indent_level += 1
        self.command.generate_code(code_generator)
        code_generator.indent_level -= 1
        code_generator.emit(f'{code_generator.indent()}}}')

class WhileCommandNode(ASTNode):
    def __init__(self, comparison, command):
        self.comparison = comparison
        self.command = command

    def generate_code(self, code_generator):
        comp_code = self.comparison.generate_code(code_generator)
        code_generator.emit(f'{code_generator.indent()}while ( {comp_code} ) {{')
        code_generator.indent_level += 1
        self.command.generate_code(code_generator)
        code_generator.indent_level -= 1
        code_generator.emit(f'{code_generator.indent()}}}')

class CompositeCommandNode(ASTNode):
    def __init__(self, commands):
        self.commands = commands

    def generate_code(self, code_generator):
        code_generator.emit(f'{code_generator.indent()}{{')
        code_generator.indent_level += 1
        for cmd in self.commands:
            cmd.generate_code(code_generator)
        code_generator.indent_level -= 1
        code_generator.emit(f'{code_generator.indent()}}}')

class ComparisonNode(ASTNode):
    def __init__(self, left, operator, right):
        self.left = left  # VariableNode
        self.operator = operator  # '==', '!=', '<'
        self.right = right  # ValueNode

    def generate_code(self, code_generator):
        left_code = self.left.generate_code(code_generator)
        right_code = self.right.generate_code(code_generator)
        return f'{left_code} {self.operator} {right_code}'

class ValueNode(ASTNode):
    def __init__(self, value):
        self.value = value  # VariableNode or NumberNode

    def generate_code(self, code_generator):
        return self.value.generate_code(code_generator)

class VariableNode(ASTNode):
    def __init__(self, name):
        self.name = name

    def generate_code(self, code_generator):
        code_generator.add_variable(self.name)
        return self.name

class NumberNode(ASTNode):
    def __init__(self, value):
        self.value = value  # String representation of the number

    def generate_code(self, code_generator):
        return self.value

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.token = self.lexer.get_next_token()

    def eat(self, token_type):
        if self.token.type == token_type:
            self.token = self.lexer.get_next_token()
        else:
            raise Exception(f'Unexpected token: {self.token.type}, expected: {token_type}')

    def program(self):
        # Program ::= Command { Command }
        commands = []
        while self.token.type != 'EOF':
            commands.append(self.command())
        return ProgramNode(commands)

    def command(self):
        # Determine which command to parse based on the current token
        if self.token.type == '=':
            return self.assign_command()
        elif self.token.type == 'G':
            return self.get_command()
        elif self.token.type == '+':
            return self.add_command()
        elif self.token.type == '-':
            return self.sub_command()
        elif self.token.type == '*':
            return self.mult_command()
        elif self.token.type == '/':
            return self.div_command()
        elif self.token.type == '%':
            return self.mod_command()
        elif self.token.type == 'P':
            return self.print_command()
        elif self.token.type == 'I':
            return self.if_command()
        elif self.token.type == 'W':
            return self.while_command()
        elif self.token.type == '{':
            return self.composite_command()
        else:
            raise Exception(f'Unknown command: {self.token.type}')

    def assign_command(self):
        # AssignCommand ::= “=” Variable Value
        self.eat('=')
        var = self.variable()
        self.eat('VARIABLE')
        val = self.value()
        return AssignCommandNode(var.name, val)

    def get_command(self):
        # GetCommand ::= “G” Variable
        self.eat('G')
        var = self.variable()
        self.eat('VARIABLE')
        return GetCommandNode(var.name)

    def add_command(self):
        # AddCommand ::= “+” Variable Value Value
        self.eat('+')
        var = self.variable()
        self.eat('VARIABLE')
        val1 = self.value()
        val2 = self.value()
        return BinaryOperationNode('+', var.name, val1, val2)

    def sub_command(self):
        # SubCommand ::= “-” Variable Value Value
        self.eat('-')
        var = self.variable()
        self.eat('VARIABLE')
        val1 = self.value()
        val2 = self.value()
        return BinaryOperationNode('-', var.name, val1, val2)

    def mult_command(self):
        # MultCommand ::= “*” Variable Value Value
        self.eat('*')
        var = self.variable()
        self.eat('VARIABLE')
        val1 = self.value()
        val2 = self.value()
        return BinaryOperationNode('*', var.name, val1, val2)

    def div_command(self):
        # DivCommand ::= “/” Variable Value Value
        self.eat('/')
        var = self.variable()
        self.eat('VARIABLE')
        val1 = self.value()
        val2 = self.value()
        return BinaryOperationNode('/', var.name, val1, val2)

    def mod_command(self):
        # ModCommand ::= “%” Variable Value Value
        self.eat('%')
        var = self.variable()
        self.eat('VARIABLE')
        val1 = self.value()
        val2 = self.value()
        return BinaryOperationNode('%', var.name, val1, val2)

    def print_command(self):
        # PrintCommand ::= “P” Value
        self.eat('P')
        val = self.value()
        return PrintCommandNode(val)

    def if_command(self):
        # IfCommand ::= “I” Comparison Command
        self.eat('I')
        comp = self.comparison()
        cmd = self.command()
        return IfCommandNode(comp, cmd)

    def while_command(self):
        # WhileCommand ::= “W” Comparison Command
        self.eat('W')
        comp = self.comparison()
        cmd = self.command()
        return WhileCommandNode(comp, cmd)

    def composite_command(self):
        # CompositeCommand ::= “{” Command { Command } “}”
        self.eat('{')
        commands = []
        while self.token.type != '}':
            commands.append(self.command())
        self.eat('}')
        return CompositeCommandNode(commands)

    def comparison(self):
        # Comparison ::= Variable Operator Value
        left = self.variable()
        self.eat('VARIABLE')
        op = self.operator()
        right = self.value()
        return ComparisonNode(left, op, right)

    def operator(self):
        # Operator ::= “=” | “<” | “#”
        if self.token.type in ('=', '<', '#'):
            op = self.token.type
            if op == '=':
                op = '=='
            elif op == '#':
                op = '!='
            self.eat(self.token.type)
            return op
        else:
            raise Exception(f'Invalid operator: {self.token.type}')

    def value(self):
        # Value ::= Variable | Number
        if self.token.type == 'VARIABLE':
            var = self.variable()
            self.eat('VARIABLE')
            return ValueNode(var)
        elif self.token.type == 'NUMBER':
            num = NumberNode(self.token.value)
            self.eat('NUMBER')
            return ValueNode(num)
        else:
            raise Exception(f'Invalid value: {self.token.type}')

    def variable(self):
        var_name = self.token.value
        return VariableNode(var_name)

class CodeGenerator:
    def __init__(self):
        self.code = []
        self.variables = set()
        self.indent_level = 1

    def indent(self):
        return '    ' * self.indent_level

    def emit(self, line):
        self.code.append(line)

    def add_variable(self, var):
        self.variables.add(var)

def main():
    import sys

    if len(sys.argv) != 3:
        print('Usage: python lps1_compiler_ast.py input.lps1 output.c')
        return

    input_filename = sys.argv[1]
    output_filename = sys.argv[2]

    # Read the input code from the input file
    with open(input_filename, 'r', encoding='utf-8') as f:
        input_code = f.read()

    # Create a lexer and parser
    lexer = Lexer(input_code)
    parser = Parser(lexer)

    # Parse the input and build the AST
    try:
        ast_root = parser.program()
    except Exception as e:
        print(f'Error: {e}')
        return

    # Generate code from the AST
    code_generator = CodeGenerator()
    ast_root.generate_code(code_generator)

    # Prepare the final C code
    variables = ', '.join(sorted(code_generator.variables))
    c_code = [
        '#include <stdio.h>',
        'int main() {',
    ]

    if variables:
        c_code.append(f'    int {variables};')
    else:
        c_code.append('    int dummy;')  # Handle case with no variables

    c_code.append('    char str[512]; // auxiliar na leitura com G')

    c_code.extend(code_generator.code)

    c_code.append('    gets(str);')  # As per the example, add this at the end
    c_code.append('    return 0;')
    c_code.append('}')

    # Write the generated C code to the output file
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(c_code))

if __name__ == '__main__':
    main()

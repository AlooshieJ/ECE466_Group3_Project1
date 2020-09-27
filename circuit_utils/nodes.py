import copy


class Value(object):
    # TODO: Add D and D' to possible values to support fault propagation
    def __init__(self, value: str):
        try:
            value = value.upper()
        except AttributeError:
            pass
        if value == 0 or value == '0':
            self.value = 0
        elif value == 1 or value == '1':
            self.value = 1
        elif value == "D":
            self.value = "D"
        elif value == "D'":
            self.value = "D'"
        else:
            self.value = 'U'

    def __eq__(self, other):
        if self.value == 1:
            if other == 1 or other == '1':
                return True
        elif self.value == 0:
            if other == 0 or other == '0':
                return True
        elif self.value == 'U':
            if other == 'U' or other == 'u':
                return True
        elif self.value == 'D':
            if other == 'd' or other == 'D':
                return True
        elif self.value == "D'":
            if other == "d'" or other == "D'":
                return True

        return False

    def __and__(self, other):
        if self == 1:
            if other == 1:
                return Value('1')
            if other == 'U':
                return Value('U')
        return Value('0')

    def __or__(self, other):
        if self == 1 or other == 1:
            return Value(1)
        if self == 'U' or other == 'U':
            return Value('U')
        return Value(0)

    def __invert__(self):
        if self == 1:
            return Value(0)
        if self == 0:
            return Value(1)
        if self == 'D':
            return Value("D'")
        if self == "D'":
            return Value('D')
        return Value('U')

    def __str__(self):
        return str(self.value)


class Gate(object):
    def __init__(self, name: str, inputs=[]):
        self.input_names = inputs
        self.input_nodes = []
        self.output_nodes = []
        self.name = name
        self.value = Value('U')
        self.value_new = Value('U')
        self.type = None
        self.logic = self.logic

    def update(self):
        self.value = self.value_new

    def logic(self):
        # Do not change
        pass


class Node(object):
    def __init__(self, gate: Gate):
        self.gate = gate
        self.name = gate.name
        self.gate_type = gate.type
        self.update = gate.update
        self.logic = gate.logic
        self.input_names = gate.input_names
        self.value = gate.value
        self.type = 'wire'
        self.output_nodes = gate.output_nodes
        self.input_nodes = gate.input_nodes

    @property
    def value_new(self):
        return self.gate.value_new

    @property
    def value(self):
        return self.gate.value

    @value.setter
    def value(self, other: Value):
        self.gate.value = other

    @value_new.setter
    def value_new(self, other: Value):
        self.gate.value_new = other

    def __eq__(self, other):
        if self.value == other:
            return True
        return False

    def __str__(self):
        return f"{str(self.type)}\t{str(self.name)} = {self.value}"

    def reset(self):
        self.value = Value('U')
        self.value_new = Value('U')

    def set(self, value: Value):
        self.value = value
        self.value_new = value


class AndGate(Gate):
    def __init__(self, name, inputs: []):
        super(AndGate, self).__init__(name, inputs)
        self.type = "AND"

    def logic(self):
        if any(node == 0 for node in self.input_nodes):
            self.value_new = Value(0)
        elif all(node == 1 for node in self.input_nodes):
            self.value_new = Value(1)
        elif all(node == 'D' or node == 1 for node in self.input_nodes):
            self.value_new = Value('D')
        elif all(node == "D'" or node == '1' for node in self.input_nodes):
            self.value_new = Value("D'")
        else:
            self.value_new = Value('U')


class NandGate(AndGate):
    def __init__(self, name, inputs: []):
        super(AndGate, self).__init__(name, inputs)
        self.type = "NAND"

    def logic(self):
        super().logic()
        self.value_new = ~self.value_new


class OrGate(Gate):
    def __init__(self, name, inputs: []):
        super(OrGate, self).__init__(name, inputs)
        self.type = "OR"

    def logic(self):
        if any(node == 1 for node in self.input_nodes):
            self.value_new = Value(1)
        elif all(node == '0' for node in self.input_nodes):
            self.value_new = Value(0)
        elif any(node == 'U' for node in self.input_nodes):
            self.value_new = Value('U')
        elif all(node == 'D' or node == 0 for node in self.input_nodes):
            self.value_new = Value('D')
        elif all(node == "D'" or node == 0 for node in self.input_nodes):
            self.value_new = Value("D'")
        else:
            self.value_new = Value(0)


class NorGate(OrGate):
    def __init__(self, name, inputs: []):
        super(OrGate, self).__init__(name, inputs)
        self.type = "NOR"

    def logic(self):
        super().logic()
        self.value_new = ~self.value_new


class NotGate(Gate):
    def __init__(self, name, inputs: []):
        super(NotGate, self).__init__(name, inputs)
        self.type = "NOT"

    def logic(self):
        self.value_new = ~self.input_nodes[0].value


class XorGate(Gate):
    def __init__(self, name, inputs: []):
        super(XorGate, self).__init__(name, inputs)
        self.type = "XOR"

    def logic(self):
        if all(node == 1 for node in self.input_nodes):
            self.value_new = Value(0)
        elif all(node == 0 for node in self.input_nodes):
            self.value_new = Value(0)
        elif any(node == 1 or node == 0 for node in self.input_nodes):
            self.value_new = Value(1)
        else:
            self.value_new = Value('U')


class XnorGate(XorGate):
    def __init__(self, name, inputs: []):
        super(XorGate, self).__init__(name, inputs)
        self.type = "XNOR"

    def logic(self):
        super().logic()
        self.value_new = ~self.value_new


class BuffGate(Gate):
    def __init__(self, name, inputs: []):
        super(BuffGate, self).__init__(name, inputs)
        self.type = "BUFF"

    def logic(self):
        self.value_new = self.input_nodes[0].value

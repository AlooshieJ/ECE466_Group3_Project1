from _collections import OrderedDict
from circuit_utils import nodes
from circuit_utils import exceptions
from re import match


class CircuitSimulator(object):
    class IterationPrinter(object):
        def generate_line(self, node: nodes.Node):
            line1 = node.type
            line2 = node.name
            line3 = node.gate_type.ljust(8) if node.gate_type else ""
            line3 += ', '.join(node.input_names)
            line4 = str(node.value)
            line = line1.ljust(11) + line2.ljust(8) + line3.ljust(20) + line4.ljust(3)
            return line

        def __init__(self, nodes):
            self.iteration = 0
            self.lines = [self.generate_line(node) for node in nodes]
            header = "Type".ljust(8) + "Variable".ljust(11) + "Logic".ljust(8) + "Inputs".ljust(9) + "Initial".ljust(3)
            self.lines.insert(0, header)

        def __iter__(self):
            for line in self.lines:
                yield line

        def __str__(self):
            string = ""
            for line in self:
                string += line + "\n"
            return string

        def __call__(self, nodes):
            self.iteration += 1
            self.lines[0] += "\t" + str(self.iteration)
            i = 0
            for node in nodes:
                self.lines[i + 1] += "\t" + str(node.value)
                i += 1

    class LineParser(object):
        def __init__(self, bench):
            self.file = bench
            self.pattern_gate = "(\S+) = ([A-Z]+)\((.+)\)"
            self.pattern_io = "([A-Z]+)\((.+)\)"
            self.gates = []
            self.input_names = []
            self.output_names = []
            self.gate_map = {"AND": nodes.AndGate, "OR": nodes.OrGate, "NAND": nodes.NandGate, "XNOR": nodes.XnorGate,
                             "NOR": nodes.NorGate, "BUFF": nodes.BuffGate, "XOR": nodes.XorGate, "NOT": nodes.NotGate}

        def parse_file(self):
            with open(self.file) as f:
                for line in f:
                    self.parse_line(line)
            return self

        def parse_line(self, line: str):
            if groups := match(self.pattern_gate, line):
                name = groups.group(1)
                gate_type = self.gate_map[groups.group(2)]
                if not gate_type:
                    raise exceptions.ParseLineError(line)
                inputs = groups.group(3).split(', ')
                self.gates.append(gate_type(name, inputs))
            elif groups := match(self.pattern_io, line):
                io = groups.group(1)
                name = groups.group(2)
                if io == "INPUT":
                    self.input_names.append(name)
                    self.gates.append(nodes.Gate(name))
                elif io == "OUTPUT":
                    self.output_names.append(name)
                else:
                    raise exceptions.ParseLineError(line)
            elif line.startswith('#') or line == '\n':
                pass
            else:
                raise exceptions.ParseLineError(line)

    class Nodes(object):
        def __init__(self):
            self.input_nodes = OrderedDict()
            self.intermediate_nodes = OrderedDict()
            self.output_nodes = OrderedDict()

        def __contains__(self, item: nodes.Node):
            if item in self.intermediate_nodes:
                return True
            if item in self.input_nodes:
                return True
            if item in self.output_nodes:
                return True
            return False

        def __getitem__(self, item: nodes.Node):
            if item in self.intermediate_nodes:
                return self.intermediate_nodes[item]
            elif item in self.input_nodes:
                return self.input_nodes[item]
            elif item in self.output_nodes:
                return self.output_nodes[item]
            return KeyError

        def __iter__(self):
            for node in self.input_nodes.values():
                yield node
            for node in self.intermediate_nodes.values():
                yield node
            for node in self.output_nodes.values():
                yield node

        def __str__(self):
            string = ''
            for node in self:
                string += f"\n{node}"
            return string

    def __init__(self, args):
        self.nodes = self.Nodes()
        self.args = args
        self.parser = self.LineParser(args.bench)
        self.compile(self.parser.parse_file())
        self.run_fault = False  # if should output fault detection
        self.fault = None

    def __next__(self):
        if self.iteration == 0:
            self.iteration += 1
            return "Inital values:" + str(self.nodes)
        self.iteration += 1
        updated_nodes = 0
        for node in self.nodes:
            node.logic()
            if node.value != node.value_new:
                updated_nodes += 1
        if updated_nodes == 0:
            raise StopIteration
        for node in self.nodes:
            node.update()
        return "Iteration # " + str(self.iteration) + ": " + str(self.nodes)

    def __iter__(self):
        self.iteration = 0
        return self

    def __str__(self):
        string = ''
        for node in self.nodes:
            string += f"{node}\n"

    def compile(self, lineparser: LineParser):
        # Compile a list of nodes from the parsed gates
        for gate in lineparser.gates:
            node = nodes.Node(gate)
            if node.name in lineparser.input_names:
                node.type = 'input'
                self.nodes.input_nodes.update({node.name: node})
            elif node.name in lineparser.output_names:
                node.type = 'output'
                self.nodes.output_nodes.update({node.name: node})
            else:
                self.nodes.intermediate_nodes.update({node.name: node})
        # Update Node member vectors input_nodes and output_nodes, which hold references to connected nodes
        for node in self.nodes:
            for input_name in node.input_names:
                self.nodes[node.name].input_nodes.append(self.nodes[input_name])
                self.nodes[input_name].output_nodes.append(self.nodes[node.name])

    def prompt(self):
        line = self.args.testvec
        if not line:
            line = input("Start simulation with input values (return to exit):")
            if not line:
                return False
        # adding D or D' implimentation
        # remove spaces
        input_values = [letter for letter in list(str(line)) if letter != ' ']
        final_inputs = []
        for chars in range(len(input_values)):  # check for D'
            if input_values[chars] != 'd' and input_values[chars] != 'D':
                if input_values[chars] != "'":
                    final_inputs.append(input_values[chars])
            else:
                D_index = chars
                if D_index + 1 < len(input_values) and input_values[D_index + 1] == "'":
                    final_inputs.append("D'")
                else:
                    final_inputs.append(input_values[chars])  # this will always be a single D
        for character, node in zip(final_inputs, self.nodes.input_nodes.values()):
            node.set(nodes.Value(character))
        self.create_fault()
        return True

    def simulate(self):
        iteration_printer = self.IterationPrinter(self.nodes)
        for iteration in self:
            iteration_printer(self.nodes)
        print(iteration_printer)

    def create_fault(self):
        while True:
            node_name = input("Which node do you want to be faulty? (return to skip) ")
            if node_name:
                try:
                    faulty_node = self.nodes[node_name]
                    while True:
                        fault_value = input(f"Which value do you want node {faulty_node.name} to be stuck at? (1/0) ")
                        if fault_value == '0':  # f Node -sA0 mean D
                            faulty_node.set(nodes.Value("D"))
                            break
                        elif fault_value == '1':  # Fault means Node = D'
                            faulty_node.set(nodes.Value("D'"))
                            break
                        else:
                            print("Invalid value: try again")
                    break
                except AttributeError as e:
                    print("Node name not found: try again")
            else:
                break

    def detect_fault(self):
        #     TODO: Detect any faults that have propagated to the outputs
        print("Fault detected by propagation of D / D'")
        if self.fault.value == nodes.Value("D"):  # SA0
            s = f"For F = {self.fault.name}-SA0"
        elif self.fault.value == nodes.Value("D'"):
            s = f"For F = {self.fault.name}-SA1"
        print(s, self.fault.name, self.fault.value)
        # if any(node == 'D' or node == "D'" for node in self.nodes.output_nodes):
        #     s = f" "
        #     #print(s)
        #     if self.fault.value == "D": # D means stuck at 0
        #         s += f"F = {self.fault.node.name} SA-0"
        #     elif self.fault.value == "D'": #D' means stuck at 1
        #         s += f"F = {self.fault.node.name} SA-1"
        #     print(s)
        #     return True
        # else:
        #     return False

    def reset(self):
        for node in self.nodes:
            node.reset()

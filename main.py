from circuit_utils import circuit_simulator
import argparse
import logging

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bench', type=str, default='circuit.bench', help='input bench file')
    parser.add_argument('-v', '--verbose', type=bool, default=True, help='verbose simulator')
    parser.add_argument('-t', '--testvec', type=str, default=None, help='test vector')
    args = parser.parse_args()

    simulator = circuit_simulator.CircuitSimulator(args)
    simulator.prompt()
    simulator.simulate()
    #if simulator.run_fault:
    #simulator.detect_fault()
    # while simulator.prompt():
    #     simulator.simulate()
    print("Finished -- bye!")

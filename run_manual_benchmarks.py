import sys
import os

# Ensure tests can import the package
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tests import test_causal_chain
from tests import test_first_light

def run_benchmarks():
    print("====================================")
    print("RMM CAUSAL CHAIN BENCHMARK")
    print("====================================")
    try:
        test_causal_chain.test_causal_chain_benchmark()
    except Exception as e:
        print(f"Test failed with error: {e}")

    print("\n====================================")
    print("RMM FIRST LIGHT BENCHMARK")
    print("====================================")
    try:
        test_first_light.test_first_light_performance()
    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    run_benchmarks()

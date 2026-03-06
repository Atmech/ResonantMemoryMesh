import sys
import os
import contextlib
import io

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tests import test_causal_chain
from tests import test_first_light

def main():
    with open('bench_data.txt', 'w') as f:
        with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            print("================ CAUSAL CHAIN ================")
            try:
                test_causal_chain.test_causal_chain_benchmark()
            except Exception as e:
                print(f"FAILED: {e}")
            
            print("================ FIRST LIGHT =================")
            try:
                test_first_light.test_first_light_performance()
            except Exception as e:
                print(f"FAILED: {e}")

if __name__ == '__main__':
    main()

import sys
from .cli import SwapifyCLI
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: swap <directory>')
        sys.exit(1)
    SwapifyCLI().run(sys.argv[1])

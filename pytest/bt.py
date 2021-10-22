

import os
import sys

print(sys.argv)

os.system("pyinstaller ./pyserve.py -F")
os.system("copy .\\dist\\pyserve.exe .\\PyTestProject\\pyserve.exe")
os.system(f".\\dist\\pyserve.exe {sys.argv[1] if len(sys.argv) > 1 else ''}")



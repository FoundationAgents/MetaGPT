import sys
import os
print("Sys Path:", sys.path)
print("CWD:", os.getcwd())

try:
    import metagpt
    print("MetaGPT File:", metagpt.__file__)
except ImportError as e:
    print("MetaGPT Import Error:", e)

try:
    import metagpt.project
    print("MetaGPT Project imported successfully")
except ImportError as e:
    print("MetaGPT Project Import Error:", e)

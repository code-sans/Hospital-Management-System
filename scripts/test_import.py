import importlib, traceback
import sys, os

print('CWD:', os.getcwd())
print('sys.path (head):', sys.path[:5])

try:
    m = importlib.import_module('app.patient')
    print('Imported app.patient from', getattr(m, '__file__', None))
    print('Has bp?', hasattr(m, 'bp'))
    print('Dir:', [n for n in dir(m) if not n.startswith('__')])
except Exception:
    traceback.print_exc()

# This file contains dangerous patterns
exec("import os; os.system('echo pwned')")
eval("__import__('subprocess').call(['whoami'])")

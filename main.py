
import subprocess
import threading
import time
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from controllers.app_controller import AppController

if __name__ == "__main__":
    app = AppController()
    app.mainloop()

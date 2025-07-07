# region Imports

# NOTE : 12/02/2025 @ 4:53 AM Just installed the fake bpy module and python module for VS Code for the first time... bruh...
# This pylint line is not really needed, but some older versions of VS Code appear to have some issues loading the fake bpy module, so I'm adding it here for anyone who uses
# VS Code as their text editor and decides to check out the inner workings of this addon's code...
# pylint: disable=fixme, import-error
import bpy
import bpy_extras
import json
import os
import struct
import bmesh
import array
import math
import mathutils
import time
from collections import namedtuple # TODO : Get rid of this fucker, namedtuples are way slower than regular tuples AND run of the mill classes, so this module was pretty much a waste of time...

import pathlib

# endregion

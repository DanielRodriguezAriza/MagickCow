# region Path Utility Functions

# All path related utility functions go here

# Append 2 paths together
# region Comments - Behaviour of path_append() vs os.path.join()

# NOTE : Behaviour of joining 2 paths mixing windows separators and unix separators:
# python's os.path.join() function has a severe issue on certain implementations when mixing '\' and '/' for path separators.
# The issue basically is that joining a path that ends with "\\" to another path in unix systems will add the "/" separator, leading to a path that looks like "\\/", rather than the correct "\\./".
# This is important since XNA uses windows separators, and that's what Magicka will use internally, but windows also supports forward slash separators, so yeah.

# NOTE : Behaviour of adding a dot when the second path starts with "/":
# What this path_append() function does is non-standard behaviour for path strings, but it is preferable to the potential issues that could come up with the actual expected behaviour.
# When the second path starts with "/" rather than "./", the meaning is "start at the root of the file system", so standard functions such as os.path.join() will discard path1 and just return path2, since
# it starts at the root of the filesystem, but we take it to mean "start relative to the current path" instead, just as "./" by adding the extra "." in between, so that we can prevent any weird issues
# from happening from slightly malformed paths, which would be bound to breaking stuff severely...
# I would rather fetch a path that does not exist relative to the working dir rather than trying to break stuff by accessing some system file relative to the system root...
# In short, this is one of the many reasons why I don't want to use os.path.join() instead on the Blender side of the code... to prevent any accidental issues where we break files we should not touch in the
# first place! Basically, this is a form of custom file sanitization logic that we have going on...

# endregion
def path_append(path1, path2):

    if len(path1) <= 0:
        return path2
    
    if len(path2) <= 0:
        return path1

    c1 = path1[-1]
    c2 = path2[0]
    
    path1_has_separator = (c1 == '/' or c1 == '\\')
    path2_has_separator = (c2 == '/' or c2 == '\\')
    
    separator = ""
    
    if path1_has_separator and path2_has_separator:
        separator = "."
    elif path1_has_separator or path2_has_separator:
        separator = ""
    else:
        separator = "/"
    
    return path1 + separator + path2

# Functions to join 2 paths
def path_join(path1, path2):
    return path_append(path1, path2)

# Function to join multiple paths
def path_join_many(paths):
    ans = ""
    for path in paths:
        ans += path_join(ans, path)
    return ans

# Get all matching paths (complex impl)
# region Comments - Behaviour of path_match_internal
# NOTE : The extension matching token is something like ".*".
# As an important side note, here's the behaviour of the 2 following cases used within this codebase:
# 1) ".*" -> returns all strings that match path_str_base/path_str_stem.any_extension
# 2) "*" -> same as above, but also includes the entry (if it exists) that has the name path_str_stem and is followed by any string or no string at all
# Basically, standard path matching tokens and wildcards, like any file system would use. But the explanation is here just in case any doubts appear in the future as for why we use ".*" rather than just "*",
# and that's because we mostly want to match for files with specific extensions, not just any random name that happens to match part of the path.
# endregion
def path_match_internal(path_str_base, path_str_stem, path_str_extension):
    path = pathlib.Path(path_str_base)
    return list(path.glob(path_str_stem + path_str_extension))

# Returns a list with all paths that match the queried string
def path_match(path_str, path_str_extension = ".*"):
    path = pathlib.Path(path_str)
    matches = list(path.parent.glob(str(path.stem) + path_str_extension))
    ans = [str(s) for s in matches] # This step is to convert from whatever operating system string struct type is used by PathLib (eg: WindowsPath) to the basic string type used by python (which can be casted to any other type later on)
    return ans

# Returns a list with all the files that match the queried string
def path_match_files(path_str):
    return [x for x in path_match(path_str) if os.path.isfile(x)]

# Returns a list with all the directories that match the queried string
def path_match_directories(path_str):
    return [x for x in path_match(path_str) if os.path.isdir(x)]

# endregion

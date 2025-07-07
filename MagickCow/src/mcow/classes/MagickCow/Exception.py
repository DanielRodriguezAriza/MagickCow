# region Exception Classes

# region Comment - Why the fuck do these exception classes exist

# The exception classes here are mostly just dummy classes that inherit directly from the Exception class without adding anything else.
# They are pretty much literally just the same as the base Python Exception class.
# They only exist to make it possible for the export and import pipelines to communicating with the main import and export Blender operator classes through the main execution try-catch block.
# This allows MagickCow specific errors to print a nicer Blender {"CANCELLED"} import / export error, while still allowing base Exceptions caused by errors in the code to print on the console
# the line on which the error took place.
# This way, different types of non-mcow errors and exceptions can be skipped in the try-catch block, which prevents catching all of the exceptions and allows us to retain debugability to a
# certain degree...
# In short, most of this stuff is just a fucking hack and does nothing special.
# Just abusing the fact that in Python it is normal for control flow to be manipulated through exceptions... Stop Iteration, anyone? lmao...

# endregion

# Base MagickCow exception class
class MagickCowException(Exception):
    pass

# Exception class for export pipeline exceptions
class MagickCowExportException(MagickCowException):
    pass

# Exception class for import pipeline exceptions
class MagickCowImportException(MagickCowException):
    pass

# Exception class for content that is not implemented yet
class MagickCowNotImplementedException(MagickCowException):
    pass

# endregion

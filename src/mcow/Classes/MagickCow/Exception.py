# region Custom Exception Classes

# Dummy exception class that is literally the same as the base Exception class.
# Only exists to make it possible for the main export exception try-catch blocks to still print the line on which the error took place when a different type of exception or error takes place.
# This way we prevent catching all of them and retain debugability to a certain degree... 
class MagickCowExportException(Exception):
    pass

# endregion

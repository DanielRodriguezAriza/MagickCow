# region Data Generation pipeline classes

# The classes within this region define the top level logic of the pipeline for data generation for MagickCow.
# The data generator classes within this region make use of the internal lower level Get Stage, Generate Stage and Make Stage classes.

class MCow_Data_Pipeline:
    def __init__(self, get_stage_generator, generate_stage_generator, make_stage_generator): # NOTE : Maybe it would make more sense to manually implement each class rather than forcing the user to define their own pipeline, which could lead to errors where the wrong logic is performed? Like, imagine some pipeline where a few extra bits of shared logic exists between steps appart from shared resource generation.
        pass
        # TODO : Implement top level / main logic here

# endregion

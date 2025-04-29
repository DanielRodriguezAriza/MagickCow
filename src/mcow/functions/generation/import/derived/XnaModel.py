# region Import Data Pipeline class - LevelModel / Map

class MCow_ImportPipeline_XnaModel(MCow_ImportPipeline):
    def __init__(self):
        super().__init__()
        return
    
    def exec(self, data):
        xna_model = data["XnbFileData"]["PrimaryObject"]
        self.import_xna_model(xna_model)

    def import_xna_model(self, xna_model):
        # TODO : Implement
        pass

# endregion

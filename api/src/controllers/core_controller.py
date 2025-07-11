from src.usecases.core_config_usecase import CoreConfigUsecase


class CoreController:
    def __init__(self):
        self.core_config_usecase = CoreConfigUsecase()

    def get_core_config(self):
        return self.core_config_usecase.get_core_config()

    def get_core_name(self):
        return self.core_config_usecase.get_core_name()

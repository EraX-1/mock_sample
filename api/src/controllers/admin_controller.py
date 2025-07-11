from src.usecases.admin_usecase import AdminUsecase


class AdminController:
    def __init__(self):
        self.admin_usecase = AdminUsecase()

    def get_admin_dashboard(self, request):
        return self.admin_usecase.get_admin_dashboard()

    def get_search_index_types(self):
        return self.admin_usecase.get_search_index_types()

    def update_search_index_type(self, index_type_id, folder_name):
        return self.admin_usecase.update_search_index_type(index_type_id, folder_name)

    def reorder_search_index_types(self, index_type_ids):
        return self.admin_usecase.reorder_search_index_types(index_type_ids)

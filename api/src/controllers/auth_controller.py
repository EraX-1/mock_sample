from src.dependencies.auth import get_current_user
from src.models.request_models import UpdateUserRoleRequest
from src.usecases.user_authentication_usecase import UserAuthenticationUsecase


class AuthController:
    def __init__(self):
        self.user_authentication_usecase = UserAuthenticationUsecase()

    def get_auth_url(self, admin_mode=False):
        return self.user_authentication_usecase.get_auth_url(admin_mode)

    async def handle_auth_callback(self, code):
        return await self.user_authentication_usecase.handle_auth_callback(code)

    def logout(self):
        return self.user_authentication_usecase.logout()

    def dropout(self, request):
        user = get_current_user(request)
        user_id = user["user_id"]
        return self.user_authentication_usecase.dropout(user_id)

    def get_user_data(self, request):
        print("request", request)
        user = get_current_user(request)
        return user

    def update_user_role(self, request, data: UpdateUserRoleRequest):
        admin_user = get_current_user(request)
        return self.user_authentication_usecase.update_user_role(
            admin_user, data.user_id, data.role
        )

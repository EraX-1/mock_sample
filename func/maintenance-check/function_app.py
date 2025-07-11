import logging
import os
import json
import azure.functions as func
from azure.appconfiguration import AzureAppConfigurationClient

app = func.FunctionApp()

# 環境変数から接続文字列を取得
app_config_connection_string = os.environ.get("AZURE_APP_CONFIG_CONNECTION_STRING")
client = AzureAppConfigurationClient.from_connection_string(
    app_config_connection_string
)


@app.function_name(name="MaintenanceStatus")
@app.route(route="maintenance_status", auth_level=func.AuthLevel.ANONYMOUS)
def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        mode_setting = client.get_configuration_setting(key="maintenance_mode")
        message_setting = client.get_configuration_setting(key="maintenance_message")

        response_data = {
            "maintenance": mode_setting.value.lower() == "true",
            "message": message_setting.value,
        }

        return func.HttpResponse(
            json.dumps(response_data, ensure_ascii=False),
            mimetype="application/json",
            status_code=200,
        )

    except Exception as e:
        logging.error(f"Error retrieving config: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to retrieve configuration."}),
            mimetype="application/json",
            status_code=500,
        )

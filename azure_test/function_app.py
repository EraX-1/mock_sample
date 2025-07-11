import logging
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="TimerTrigger")
@app.schedule(schedule="*/5 * * * * *", arg_name="mytimer", run_on_startup=True, use_monitor=True)
def timer_trigger(mytimer: func.TimerRequest) -> None:
    logging.info("Azure Function container test: Timer trigger executed.")
    print("Hello from Azure Function container!")
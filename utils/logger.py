import datetime

def log(message: str):
    """
    Append a log message to the app.log file with a timestamp.

    Args:
        message (str): The message to log.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("app.log", "a") as f:
        f.write(f"[{now}] {message}\n")

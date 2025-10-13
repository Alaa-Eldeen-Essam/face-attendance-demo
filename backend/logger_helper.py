import logging
import time
from fastapi import Request
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import gzip
import shutil
import os

LOG_FILE = "request_performance.log"
LOG_MAX_SIZE = 20 * 1024 * 1024  # 20 MB
LOG_BACKUP_COUNT = 5             # Keep last 5 log files

def setup_logger():
    """
    Configure rotating and timed log handler.
    Rotation:
      - Weekly (every Monday at midnight)
      - Max file size: 20 MB
      - Automatically compresses old logs
    """
    logger = logging.getLogger("performance_logger")
    logger.setLevel(logging.INFO)

    # Use a TimedRotatingFileHandler (weekly rotation)
    handler = TimedRotatingFileHandler(
        LOG_FILE,
        when="W0",             # Rotate weekly (Monday)
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8"
    )

    # Set a max size limit using RotatingFileHandler logic manually
    def shouldRollover(handler, record):
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) >= LOG_MAX_SIZE:
            return True
        return False

    old_emit = handler.emit
    def emit_with_size_check(record):
        if shouldRollover(handler, record):
            handler.doRollover()
        old_emit(record)

    handler.emit = emit_with_size_check
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    # Attach compression on rollover
    def compress_old_log(source_path):
        if os.path.exists(source_path):
            compressed_path = f"{source_path}.gz"
            with open(source_path, "rb") as f_in, gzip.open(compressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.remove(source_path)

    old_doRollover = handler.doRollover
    def doRollover_and_compress():
        old_doRollover()
        # Compress previous log files
        for file in os.listdir(os.path.dirname(LOG_FILE) or "."):
            if file.startswith(os.path.basename(LOG_FILE)) and not file.endswith(".gz"):
                file_path = os.path.join(os.path.dirname(LOG_FILE) or ".", file)
                if os.path.isfile(file_path):
                    compress_old_log(file_path)

    handler.doRollover = doRollover_and_compress

    logger.addHandler(handler)
    return logger


def create_logging_middleware(app, logger):
    """
    Adds a middleware to log request & response time, IP, and bodies.
    """
    @app.middleware("http")
    async def log_request_response_time(request: Request, call_next):
        start_time = time.perf_counter()
        client_ip = request.client.host
        method = request.method
        path = request.url.path

        try:
            body_bytes = await request.body()
            request_body = body_bytes.decode("utf-8") if body_bytes else ""
        except Exception:
            request_body = "<Failed to read body>"

        response = await call_next(request)
        process_time = time.perf_counter() - start_time

        try:
            response_body = response.body.decode("utf-8") if hasattr(response, "body") else "<Streaming>"
        except Exception:
            response_body = "<Failed to read response body>"

        log_message = (
            f"IP={client_ip} | {method} {path} | Status={response.status_code} | "
            f"Time={process_time:.4f}s | RequestBody={request_body} | ResponseBody={response_body}"
        )

        logger.info(log_message)
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        return response

    return app

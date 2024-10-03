import logging
import os
import socket
from logging.handlers import SysLogHandler

from dotenv import load_dotenv

load_dotenv()

# Logging initialization
class ContextFilter(logging.Filter):
    hostname: str = socket.gethostname()
    def filter(self, record):
        record.hostname = ContextFilter.hostname
        return True
    
syslog_url = os.getenv('PAPERTRAIL_LOG_DESTINATION', os.getenv('LOG_DESTINATION', 'localhost')) # Backwards compatible with the original papertrail setup
syslog_port = int(os.getenv('PAPERTRAIL_LOG_PORT', os.getenv('LOG_PORT', 514))) # Backwards compatible with the original papertrail setup
syslogaddress = (syslog_url, syslog_port)
syslog = SysLogHandler(address=syslogaddress, facility=SysLogHandler.LOG_USER)
syslog.addFilter(ContextFilter())
format = '%(asctime)s %(hostname)s cia_bot: %(message)s'
formatter = logging.Formatter(format, datefmt='%b %d %H:%M:%S')
syslog.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(syslog)
logger.setLevel(logging.INFO)
# End logging initialization
 
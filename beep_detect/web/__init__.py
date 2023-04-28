from waitress import serve
from .app import app
import logging

logger = logging.getLogger('waitress')
logger.setLevel(logging.DEBUG)

serve(app, host='0.0.0.0', port=8080)
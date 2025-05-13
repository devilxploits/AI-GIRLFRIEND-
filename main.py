import os
import logging
from app import app

# Just import views to register the routes
from views import *

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

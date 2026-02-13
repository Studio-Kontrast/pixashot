import os
from dotenv import load_dotenv
from logging.config import dictConfig
from datetime import datetime
import time
import psutil
import logging

from quart import Quart, request, make_response
from quart_rate_limiter import RateLimiter
from playwright.async_api import async_playwright

from cache_manager import CacheManager
from config import config, get_logging_config
from capture_service import CaptureService
from routes import register_routes
from context_manager import ContextManager

logger = logging.getLogger(__name__)

# src/app.py (relevant section)

class AppContainer:
    def __init__(self):
        self.playwright = None
        self.capture_service = None
        self.cache_manager = None
        self.rate_limiter = None

    async def initialize(self):
        try:
            # Start playwright
            self.playwright = await async_playwright().start()

            # Initialize capture service
            self.capture_service = CaptureService()
            await self.capture_service.initialize(self.playwright)

            # Initialize cache manager
            self.cache_manager = CacheManager(
                max_size=config.CACHE_MAX_SIZE if config.CACHE_MAX_SIZE > 0 else None
            )
        except Exception as e:
            logger.error(f"Failed to initialize AppContainer: {str(e)}")
            raise

    async def close(self):
        if self.capture_service:
            await self.capture_service.close()
        if self.playwright:
            await self.playwright.stop()


def create_app():
    dictConfig(get_logging_config())
    app = Quart(__name__)

    # Create container with just the essentials
    container = AppContainer()
    app.config['container'] = container

    # Initialize rate limiter
    container.rate_limiter = RateLimiter(app)

    # Configure caching
    app.config['CACHING_ENABLED'] = config.CACHE_MAX_SIZE > 0
    if app.config['CACHING_ENABLED']:
        app.logger.info(f"Caching enabled with max size: {config.CACHE_MAX_SIZE}")
    else:
        app.logger.info("Caching disabled")

    # Register startup and shutdown handlers
    @app.before_serving
    async def startup():
        app.config['start_time'] = time.time()
        await container.initialize()

    @app.after_serving
    async def shutdown():
        await container.close()

    # Register routes
    register_routes(app)

    def _parse_csv(value: str):
        return [item.strip() for item in value.split(',') if item.strip()]

    def _resolve_allowed_origin(origin: str):
        allowed_origins = _parse_csv(config.CORS_ALLOWED_ORIGINS)
        if '*' in allowed_origins:
            return '*'
        if origin in allowed_origins:
            return origin
        return None

    @app.before_request
    async def handle_cors_preflight():
        if not config.CORS_ENABLED:
            return None

        if request.method != 'OPTIONS':
            return None

        origin = request.headers.get('Origin')
        allowed_origin = _resolve_allowed_origin(origin) if origin else None
        if origin and not allowed_origin:
            return make_response('', 403)

        response = await make_response('', 204)
        if allowed_origin:
            response.headers['Access-Control-Allow-Origin'] = allowed_origin
            response.headers['Vary'] = 'Origin'

        response.headers['Access-Control-Allow-Methods'] = config.CORS_ALLOWED_METHODS
        response.headers['Access-Control-Allow-Headers'] = config.CORS_ALLOWED_HEADERS
        if config.CORS_ALLOW_CREDENTIALS:
            response.headers['Access-Control-Allow-Credentials'] = 'true'

        return response

    @app.after_request
    async def add_cors_headers(response):
        if not config.CORS_ENABLED:
            return response

        origin = request.headers.get('Origin')
        if not origin:
            return response

        allowed_origin = _resolve_allowed_origin(origin)
        if not allowed_origin:
            return response

        response.headers['Access-Control-Allow-Origin'] = allowed_origin
        response.headers['Vary'] = 'Origin'
        response.headers['Access-Control-Allow-Methods'] = config.CORS_ALLOWED_METHODS
        response.headers['Access-Control-Allow-Headers'] = config.CORS_ALLOWED_HEADERS
        if config.CORS_ALLOW_CREDENTIALS:
            response.headers['Access-Control-Allow-Credentials'] = 'true'

        return response

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.PORT, debug=True)

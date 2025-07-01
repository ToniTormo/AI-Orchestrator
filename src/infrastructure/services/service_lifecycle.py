"""
Service Lifecycle Management

Abstract base classes for services that require initialization and shutdown lifecycle management.
These utilities provide standard patterns for async service management with proper error handling and logging.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional
from src.utils.logging import setup_logger
from src.utils.exceptions_control import create_error

class ServiceLifecycleError(Exception):
    """Base exception for service lifecycle errors"""
    pass

class AsyncServiceBase(ABC):
    """
    Abstract base class for services that require async lifecycle management.
    Provides standard initialize/shutdown pattern with error handling and logging.
    """
    
    def __init__(self, service_name: str, log_level: Optional[str] = None):
        """
        Initialize the service base
        
        Args:
            service_name: Name of the service for logging purposes
            log_level: Optional specific log level for this service
        """
        self.service_name = service_name
        
        # Import settings here to avoid circular import at module level
        if log_level is None:
            try:
                from src.config import settings
                log_level = settings.logging.module_levels.get(service_name.split('.')[0], settings.logging.level)
            except ImportError:
                log_level = "INFO"  # Default fallback
        
        self.logger = setup_logger(service_name, log_level)
        self._initialized = False
        self._init_lock = asyncio.Lock()
    
    async def initialize(self):
        """
        Initialize the service with thread-safe initialization
        """
        async with self._init_lock:
            if self._initialized:
                self.logger.debug(f"[{self.service_name}] Already initialized")
                return
            
            try:
                await self._initialize_impl()
                self._initialized = True
                self.logger.info(f"[{self.service_name}] Initialization completed")
            except Exception as e:
                raise create_error(ServiceLifecycleError, f"Failed to initialize {self.service_name}: {e}", self.service_name)
    
    async def shutdown(self):
        """
        Shutdown the service with thread-safe shutdown
        """
        async with self._init_lock:
            if not self._initialized:
                self.logger.debug(f"[{self.service_name}] Not initialized, skipping shutdown")
                return
            
            try:
                await self._shutdown_impl()
                self._initialized = False
                self.logger.info(f"[{self.service_name}] Shutdown completed")
            except Exception as e:
                # Mark as not initialized even if shutdown fails to prevent deadlock
                self._initialized = False
                raise create_error(ServiceLifecycleError, f"Failed to shutdown {self.service_name}: {e}", self.service_name)
    
    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized"""
        return self._initialized

    @abstractmethod
    async def _initialize_impl(self):
        """
        Implementation-specific initialization logic
        Subclasses must implement this method
        """
        pass
    
    @abstractmethod
    async def _shutdown_impl(self):
        """
        Implementation-specific shutdown logic
        Subclasses must implement this method
        """
        pass

class SimpleAsyncService(AsyncServiceBase):
    """
    Simple async service base for services that don't need complex initialization/shutdown
    """
    
    async def _initialize_impl(self):
        """Default empty initialization"""
        pass
    
    async def _shutdown_impl(self):
        """Default empty shutdown"""
        pass 
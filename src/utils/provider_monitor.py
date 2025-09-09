"""Provider health monitoring and management."""

import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from .logging import logger

class ProviderStatus(Enum):
    """Provider health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ProviderHealth:
    """Provider health information."""
    name: str
    status: ProviderStatus = ProviderStatus.UNKNOWN
    success_count: int = 0
    failure_count: int = 0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    consecutive_failures: int = 0
    error_types: Set[str] = None
    
    def __post_init__(self):
        if self.error_types is None:
            self.error_types = set()
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total
    
    @property
    def is_reliable(self) -> bool:
        """Check if provider is reliable."""
        # Consider reliable if success rate > 70% and recent activity
        if self.success_rate < 0.7:
            return False
        
        # Check if had recent success (within last hour)
        if self.last_success is None:
            return False
        
        return (time.time() - self.last_success) < 3600  # 1 hour
    
    def update_status(self):
        """Update status based on current metrics."""
        if self.consecutive_failures >= 5:
            self.status = ProviderStatus.UNHEALTHY
        elif self.consecutive_failures >= 3 or self.success_rate < 0.5:
            self.status = ProviderStatus.DEGRADED
        elif self.success_rate >= 0.7:
            self.status = ProviderStatus.HEALTHY
        else:
            self.status = ProviderStatus.UNKNOWN

class ProviderMonitor:
    """Monitor and manage provider health."""
    
    def __init__(self):
        self.providers: Dict[str, ProviderHealth] = {}
        self.blacklisted_providers: Set[str] = {
            "Chatai",  # Known to return 401 errors
            "OpenaiChat",  # Requires Chrome browser
        }
    
    def get_provider_health(self, provider_name: str) -> ProviderHealth:
        """Get health information for a provider."""
        if provider_name not in self.providers:
            self.providers[provider_name] = ProviderHealth(name=provider_name)
        return self.providers[provider_name]
    
    def record_success(self, provider_name: str):
        """Record a successful API call."""
        health = self.get_provider_health(provider_name)
        health.success_count += 1
        health.last_success = time.time()
        health.consecutive_failures = 0
        health.update_status()
        
        logger.debug(f"Provider {provider_name}: success recorded (rate: {health.success_rate:.2f})")
    
    def record_failure(self, provider_name: str, error_type: str = "unknown"):
        """Record a failed API call."""
        health = self.get_provider_health(provider_name)
        health.failure_count += 1
        health.last_failure = time.time()
        health.consecutive_failures += 1
        health.error_types.add(error_type)
        health.update_status()
        
        logger.debug(f"Provider {provider_name}: failure recorded (rate: {health.success_rate:.2f}, consecutive: {health.consecutive_failures})")
    
    def get_healthy_providers(self, available_providers: Dict[str, any]) -> List[str]:
        """Get list of healthy providers."""
        healthy = []
        
        for provider_name in available_providers:
            if provider_name == "Auto":
                continue
            
            if provider_name in self.blacklisted_providers:
                continue
            
            health = self.get_provider_health(provider_name)
            
            # Include provider if it's healthy or unknown (give it a chance)
            if health.status in [ProviderStatus.HEALTHY, ProviderStatus.UNKNOWN]:
                healthy.append(provider_name)
            elif health.status == ProviderStatus.DEGRADED and health.consecutive_failures < 3:
                # Give degraded providers a chance if not too many consecutive failures
                healthy.append(provider_name)
        
        return healthy
    
    def get_reliable_providers(self, available_providers: Dict[str, any]) -> List[str]:
        """Get list of most reliable providers."""
        reliable = []
        
        for provider_name in available_providers:
            if provider_name == "Auto":
                continue
            
            if provider_name in self.blacklisted_providers:
                continue
            
            health = self.get_provider_health(provider_name)
            if health.is_reliable:
                reliable.append(provider_name)
        
        # Sort by success rate
        reliable.sort(key=lambda p: self.get_provider_health(p).success_rate, reverse=True)
        
        # Add some known reliable providers if list is empty
        if not reliable:
            fallback_providers = ["DuckDuckGo", "Blackbox", "DeepInfra", "PerplexityLabs"]
            for provider in fallback_providers:
                if provider in available_providers and provider not in self.blacklisted_providers:
                    reliable.append(provider)
        
        return reliable
    
    def is_provider_blacklisted(self, provider_name: str) -> bool:
        """Check if provider is blacklisted."""
        return provider_name in self.blacklisted_providers
    
    def blacklist_provider(self, provider_name: str, reason: str = ""):
        """Add provider to blacklist."""
        self.blacklisted_providers.add(provider_name)
        logger.warning(f"Provider {provider_name} blacklisted: {reason}")
    
    def get_status_summary(self) -> Dict[str, any]:
        """Get summary of all provider statuses."""
        summary = {
            "healthy": [],
            "degraded": [],
            "unhealthy": [],
            "blacklisted": list(self.blacklisted_providers)
        }
        
        for provider_name, health in self.providers.items():
            if health.status == ProviderStatus.HEALTHY:
                summary["healthy"].append({
                    "name": provider_name,
                    "success_rate": health.success_rate,
                    "total_calls": health.success_count + health.failure_count
                })
            elif health.status == ProviderStatus.DEGRADED:
                summary["degraded"].append({
                    "name": provider_name,
                    "success_rate": health.success_rate,
                    "consecutive_failures": health.consecutive_failures
                })
            elif health.status == ProviderStatus.UNHEALTHY:
                summary["unhealthy"].append({
                    "name": provider_name,
                    "consecutive_failures": health.consecutive_failures,
                    "error_types": list(health.error_types)
                })
        
        return summary

# Global provider monitor instance
provider_monitor = ProviderMonitor()

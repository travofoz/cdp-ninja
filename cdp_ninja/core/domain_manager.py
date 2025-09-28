"""
CDP Domain Manager - Lazy loading and lifecycle management for CDP domains
Provides intelligent domain loading with stealth-conscious configuration
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Set, List, Optional, Callable
from threading import Lock

logger = logging.getLogger(__name__)


class CDPDomain(Enum):
    """Extended CDP Protocol Domains for Phase 3"""
    # Existing stealth-safe domains (Phase 1-2)
    NETWORK = "Network"
    RUNTIME = "Runtime"
    PAGE = "Page"
    DOM = "DOM"
    CONSOLE = "Console"

    # New domains for Phase 3
    PERFORMANCE = "Performance"          # Medium stealth risk
    SECURITY = "Security"               # Medium stealth risk
    ACCESSIBILITY = "Accessibility"     # High stealth risk
    HEAPPROFILER = "HeapProfiler"       # Very high stealth risk
    PROFILER = "Profiler"               # Very high stealth risk
    DOMDEBUGGER = "DOMDebugger"         # High stealth risk
    SERVICEWORKER = "ServiceWorker"     # Medium stealth risk (if available)
    FETCH = "Fetch"                     # Low stealth risk
    INPUT = "Input"                     # Low stealth risk (no enable needed)
    MEMORY = "Memory"                   # High stealth risk


class DomainRiskLevel(Enum):
    """Stealth risk assessment for domains"""
    SAFE = "safe"           # Stealth-tested, no detection risk
    LOW = "low"             # Minimal detection risk
    MEDIUM = "medium"       # Moderate detection risk
    HIGH = "high"           # High detection risk
    VERY_HIGH = "very_high" # Maximum detection risk


@dataclass
class DomainConfig:
    """Configuration for a CDP domain"""
    domain: CDPDomain
    risk_level: DomainRiskLevel
    requires_enable: bool = True
    dependencies: List[CDPDomain] = None
    auto_unload_timeout: Optional[int] = None  # Minutes until auto-unload

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class DomainState:
    """Runtime state of a CDP domain"""
    enabled: bool = False
    last_used: float = 0
    enable_count: int = 0
    last_error: Optional[str] = None
    enabled_by: Set[str] = None

    def __post_init__(self):
        if self.enabled_by is None:
            self.enabled_by = set()


class DomainManager:
    """Intelligent CDP domain lifecycle management"""

    # Domain configurations with risk assessments
    DOMAIN_CONFIGS = {
        # Stealth-safe domains (proven)
        CDPDomain.NETWORK: DomainConfig(CDPDomain.NETWORK, DomainRiskLevel.SAFE),
        CDPDomain.RUNTIME: DomainConfig(CDPDomain.RUNTIME, DomainRiskLevel.SAFE),
        CDPDomain.PAGE: DomainConfig(CDPDomain.PAGE, DomainRiskLevel.SAFE),
        CDPDomain.DOM: DomainConfig(CDPDomain.DOM, DomainRiskLevel.SAFE),
        CDPDomain.CONSOLE: DomainConfig(CDPDomain.CONSOLE, DomainRiskLevel.SAFE),

        # New domains by risk level
        CDPDomain.FETCH: DomainConfig(CDPDomain.FETCH, DomainRiskLevel.LOW),
        CDPDomain.INPUT: DomainConfig(CDPDomain.INPUT, DomainRiskLevel.LOW, requires_enable=False),

        CDPDomain.PERFORMANCE: DomainConfig(CDPDomain.PERFORMANCE, DomainRiskLevel.MEDIUM, auto_unload_timeout=15),
        CDPDomain.SECURITY: DomainConfig(CDPDomain.SECURITY, DomainRiskLevel.MEDIUM, auto_unload_timeout=10),
        CDPDomain.SERVICEWORKER: DomainConfig(CDPDomain.SERVICEWORKER, DomainRiskLevel.MEDIUM, auto_unload_timeout=20),

        CDPDomain.ACCESSIBILITY: DomainConfig(CDPDomain.ACCESSIBILITY, DomainRiskLevel.HIGH, auto_unload_timeout=5),
        CDPDomain.DOMDEBUGGER: DomainConfig(CDPDomain.DOMDEBUGGER, DomainRiskLevel.HIGH, auto_unload_timeout=5),
        CDPDomain.MEMORY: DomainConfig(CDPDomain.MEMORY, DomainRiskLevel.HIGH, auto_unload_timeout=10),

        CDPDomain.HEAPPROFILER: DomainConfig(CDPDomain.HEAPPROFILER, DomainRiskLevel.VERY_HIGH, auto_unload_timeout=3),
        CDPDomain.PROFILER: DomainConfig(CDPDomain.PROFILER, DomainRiskLevel.VERY_HIGH, auto_unload_timeout=3),
    }

    def __init__(self, max_risk_level: DomainRiskLevel = DomainRiskLevel.MEDIUM):
        """
        Initialize domain manager

        @param max_risk_level - Maximum risk level to allow (stealth configuration)
        """
        self.max_risk_level = max_risk_level
        self.domain_states: Dict[CDPDomain, DomainState] = {}
        self.cdp_client = None  # Set by pool when needed
        self._lock = Lock()
        self.enabled_domains: Set[CDPDomain] = set()
        self.auto_unload_enabled = True  # Can be disabled via CLI
        self.default_timeout_minutes = 15  # Default timeout for domains

        # Initialize domain states
        for domain in CDPDomain:
            self.domain_states[domain] = DomainState()

    def set_cdp_client(self, cdp_client):
        """Set CDP client for domain operations"""
        self.cdp_client = cdp_client

    def can_enable_domain(self, domain: CDPDomain) -> bool:
        """Check if domain can be enabled based on risk settings"""
        config = self.DOMAIN_CONFIGS.get(domain)
        if not config:
            return False

        # Check risk level
        risk_levels = [DomainRiskLevel.SAFE, DomainRiskLevel.LOW, DomainRiskLevel.MEDIUM,
                      DomainRiskLevel.HIGH, DomainRiskLevel.VERY_HIGH]

        max_index = risk_levels.index(self.max_risk_level)
        domain_index = risk_levels.index(config.risk_level)

        return domain_index <= max_index

    def ensure_domain(self, domain: CDPDomain, caller: str = "unknown") -> bool:
        """
        Ensure domain is enabled, with lazy loading

        @param domain - Domain to ensure is enabled
        @param caller - Identifier of the caller (for tracking)
        @returns True if domain is available
        """
        with self._lock:
            # Check if already enabled
            if self.domain_states[domain].enabled:
                self._update_domain_usage(domain, caller)
                return True

            # Check if we can enable this domain
            if not self.can_enable_domain(domain):
                logger.warning(f"Domain {domain.value} blocked by risk level ({self.max_risk_level.value})")
                return False

            # Enable dependencies first
            config = self.DOMAIN_CONFIGS.get(domain)
            if config and config.dependencies:
                for dep_domain in config.dependencies:
                    if not self.ensure_domain(dep_domain, f"{caller}:dep"):
                        logger.error(f"Failed to enable dependency {dep_domain.value} for {domain.value}")
                        return False

            # Enable the domain
            return self._enable_domain(domain, caller)

    def _enable_domain(self, domain: CDPDomain, caller: str) -> bool:
        """Internal domain enabling logic"""
        config = self.DOMAIN_CONFIGS.get(domain)
        if not config:
            logger.error(f"Unknown domain: {domain.value}")
            return False

        state = self.domain_states[domain]

        try:
            # Enable domain if required
            if config.requires_enable and self.cdp_client:
                result = self.cdp_client.send_command(f"{domain.value}.enable", timeout=10)

                if 'error' in result:
                    error_msg = result.get('error', 'Unknown error')
                    logger.warning(f"Failed to enable {domain.value}: {error_msg}")
                    state.last_error = error_msg
                    return False

            # Mark as enabled
            state.enabled = True
            state.enable_count += 1
            state.last_error = None
            state.enabled_by.add(caller)
            self.enabled_domains.add(domain)
            self._update_domain_usage(domain, caller)

            logger.info(f"Enabled domain {domain.value} (risk: {config.risk_level.value}, caller: {caller})")
            return True

        except Exception as e:
            logger.error(f"Exception enabling {domain.value}: {e}")
            state.last_error = str(e)
            return False

    def _update_domain_usage(self, domain: CDPDomain, caller: str):
        """Update domain usage tracking"""
        state = self.domain_states[domain]
        state.last_used = time.time()
        state.enabled_by.add(caller)

    def disable_domain(self, domain: CDPDomain, force: bool = False) -> bool:
        """
        Disable a domain (careful - may break ongoing operations)

        @param domain - Domain to disable
        @param force - Force disable even if other callers are using it
        @returns True if disabled
        """
        with self._lock:
            state = self.domain_states[domain]

            if not state.enabled:
                return True

            if not force and len(state.enabled_by) > 1:
                logger.info(f"Not disabling {domain.value} - still used by {len(state.enabled_by)} callers")
                return False

            config = self.DOMAIN_CONFIGS.get(domain)
            if config and config.requires_enable and self.cdp_client:
                result = self.cdp_client.send_command(f"{domain.value}.disable", timeout=5)
                if 'error' in result:
                    logger.warning(f"Failed to disable {domain.value}: {result.get('error')}")

            state.enabled = False
            state.enabled_by.clear()
            self.enabled_domains.discard(domain)

            logger.info(f"Disabled domain {domain.value}")
            return True

    def get_domain_status(self) -> Dict[str, any]:
        """Get comprehensive domain status"""
        with self._lock:
            status = {
                "max_risk_level": self.max_risk_level.value,
                "enabled_domains": [d.value for d in self.enabled_domains],
                "domain_details": {}
            }

            for domain, state in self.domain_states.items():
                config = self.DOMAIN_CONFIGS.get(domain)
                status["domain_details"][domain.value] = {
                    "enabled": state.enabled,
                    "risk_level": config.risk_level.value if config else "unknown",
                    "can_enable": self.can_enable_domain(domain),
                    "last_used": state.last_used,
                    "enable_count": state.enable_count,
                    "enabled_by": list(state.enabled_by),
                    "last_error": state.last_error
                }

            return status

    def cleanup_unused_domains(self, max_age_minutes: int = 15) -> int:
        """
        Clean up domains that haven't been used recently

        @param max_age_minutes - Domains unused for this long will be disabled
        @returns Number of domains disabled
        """
        current_time = time.time()
        cleanup_count = 0

        with self._lock:
            for domain, state in self.domain_states.items():
                if not state.enabled:
                    continue

                config = self.DOMAIN_CONFIGS.get(domain)
                if not config or config.risk_level == DomainRiskLevel.SAFE:
                    continue  # Don't auto-cleanup safe domains

                # Check if domain has specific timeout
                timeout_minutes = config.auto_unload_timeout or max_age_minutes
                age_minutes = (current_time - state.last_used) / 60

                if age_minutes > timeout_minutes:
                    if self.disable_domain(domain, force=False):
                        cleanup_count += 1
                        logger.info(f"Auto-disabled unused domain {domain.value} (unused for {age_minutes:.1f}m)")

        return cleanup_count

    def enable_default_domains(self) -> bool:
        """Enable the default safe domains"""
        safe_domains = [
            CDPDomain.NETWORK,
            CDPDomain.RUNTIME,
            CDPDomain.PAGE,
            CDPDomain.DOM,
            CDPDomain.CONSOLE
        ]

        success_count = 0
        for domain in safe_domains:
            if self.ensure_domain(domain, "default_startup"):
                success_count += 1

        logger.info(f"Enabled {success_count}/{len(safe_domains)} default domains")
        return success_count == len(safe_domains)

    def set_risk_level(self, new_level: DomainRiskLevel):
        """Update maximum risk level (runtime configuration)"""
        old_level = self.max_risk_level
        self.max_risk_level = new_level
        logger.info(f"Updated max risk level: {old_level.value} -> {new_level.value}")

        # If we reduced risk level, disable domains that are now too risky
        if new_level.value != old_level.value:
            with self._lock:
                to_disable = []
                for domain in self.enabled_domains:
                    if not self.can_enable_domain(domain):
                        to_disable.append(domain)

                for domain in to_disable:
                    self.disable_domain(domain, force=True)
                    logger.info(f"Disabled {domain.value} due to reduced risk tolerance")

    def set_auto_unload_enabled(self, enabled: bool):
        """Enable or disable automatic domain unloading"""
        self.auto_unload_enabled = enabled
        logger.info(f"Auto-unload {'enabled' if enabled else 'disabled'}")

    def set_default_timeout(self, timeout_minutes: int):
        """Set default timeout for domains without specific timeouts"""
        self.default_timeout_minutes = timeout_minutes
        logger.info(f"Default domain timeout set to {timeout_minutes} minutes")

    def enable_all_allowed_domains(self):
        """Enable all domains that are allowed by current risk level (eager loading)"""
        enabled_count = 0
        for domain in CDPDomain:
            if self.can_enable_domain(domain):
                if self.ensure_domain(domain, "eager_load"):
                    enabled_count += 1

        logger.info(f"Eager loading: enabled {enabled_count} domains")
        return enabled_count


# Global domain manager instance
_global_domain_manager = None
_domain_manager_lock = Lock()


def get_domain_manager() -> DomainManager:
    """Get or create global domain manager"""
    global _global_domain_manager

    with _domain_manager_lock:
        if _global_domain_manager is None:
            _global_domain_manager = DomainManager()
        return _global_domain_manager


def initialize_domain_manager(max_risk_level: DomainRiskLevel = DomainRiskLevel.MEDIUM) -> DomainManager:
    """Initialize global domain manager with configuration"""
    global _global_domain_manager

    with _domain_manager_lock:
        _global_domain_manager = DomainManager(max_risk_level)
        logger.info(f"Initialized domain manager with max risk level: {max_risk_level.value}")
        return _global_domain_manager


def shutdown_domain_manager():
    """Shutdown global domain manager"""
    global _global_domain_manager

    with _domain_manager_lock:
        if _global_domain_manager:
            # Cleanup all non-safe domains
            cleanup_count = 0
            for domain in list(_global_domain_manager.enabled_domains):
                config = _global_domain_manager.DOMAIN_CONFIGS.get(domain)
                if config and config.risk_level != DomainRiskLevel.SAFE:
                    if _global_domain_manager.disable_domain(domain, force=True):
                        cleanup_count += 1

            logger.info(f"Shutdown domain manager, disabled {cleanup_count} domains")
            _global_domain_manager = None
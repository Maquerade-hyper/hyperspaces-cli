class HyperspaceError(Exception):
    """Base exception for Hyperspace."""


class ConfigurationError(HyperspaceError):
    pass


class NodeError(HyperspaceError):
    pass


class ServiceError(HyperspaceError):
    pass
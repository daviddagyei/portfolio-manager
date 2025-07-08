from enum import Enum


class PortfolioType(str, Enum):
    """Portfolio types supported by the system."""
    PERSONAL = "personal"
    RETIREMENT = "retirement"
    EDUCATION = "education"
    INVESTMENT = "investment"
    TRADING = "trading"
    OTHER = "other"

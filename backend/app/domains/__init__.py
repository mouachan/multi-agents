"""The business domains of the platform (see spec.py). Register a new domain in DOMAINS."""
from typing import Dict, List

from app.domains.claims import CLAIMS
from app.domains.postal import POSTAL
from app.domains.spec import DomainSpec
from app.domains.tenders import TENDERS

DOMAINS: Dict[str, DomainSpec] = {spec.name: spec for spec in (CLAIMS, TENDERS, POSTAL)}


def get_domain(name: str) -> DomainSpec:
    """The domain called `name` (KeyError for an unknown domain)."""
    return DOMAINS[name]


def domain_of_entity(entity: str) -> DomainSpec:
    """The domain whose cases are `entity` ("claim" -> claims)."""
    return next(spec for spec in DOMAINS.values() if spec.entity == entity)


def all_domains() -> List[DomainSpec]:
    return list(DOMAINS.values())


__all__ = ["DomainSpec", "DOMAINS", "get_domain", "domain_of_entity", "all_domains"]

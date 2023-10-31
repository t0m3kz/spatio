"""Init Jobs"""
from nautobot.core.celery import register_jobs
from .deploy_site import NewBranch
from .deploy_tenant import NewTenant
from .deploy_epg import NewEpg

jobs = [NewBranch, NewTenant, NewEpg]
register_jobs(*jobs)

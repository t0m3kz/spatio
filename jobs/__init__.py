"""Init Jobs"""
from nautobot.core.celery import register_jobs
from .deploy_site import NewBranch
from .deploy_tenant import NewTenant

jobs = [NewBranch, NewTenant]
register_jobs(*jobs)

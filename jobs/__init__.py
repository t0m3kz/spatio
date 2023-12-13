"""Init Jobs"""
from nautobot.core.celery import register_jobs
from .deploy_site import NewBranch
from .deploy_tenant import NewTenant
from .deploy_epg import NewEpg
from .deploy_bd import NewBd
from .aci_tenant import AciTenant

jobs = [NewBranch, NewTenant, NewEpg, NewBd, AciTenant]
register_jobs(*jobs)

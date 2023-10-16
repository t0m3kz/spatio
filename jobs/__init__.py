"""Init Jobs"""
from nautobot.core.celery import register_jobs
from .deploy_site import NewBranch


jobs = [NewBranch]
register_jobs(*jobs)

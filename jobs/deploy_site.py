"""Branch Job"""
from nautobot.core.celery import register_jobs
from nautobot.extras.jobs import Job, StringVar
from nautobot.dcim.models import Location


name = "Deployment Jobs"

class NewBranch(Job):
    """
    System job to clone and/or pull a Git repository, then invoke `refresh_datasource_content()`.
    """

    field_order = ["site_name", "switch_count", "switch_model"]
    site_name = StringVar(description="Name of the new site")

    class Meta:
        """Meta class."""
        name = "New Branch"
        description = "Provision a new branch site"
        has_sensitive_variables = False


    def run(self, data):
        """Execute Job."""

        job_result = self.job_result
        self.logger.info("Creating new branch office...")

        try:
            site = Location(
                name=data["site_name"],
            )
            site.validated_save()
        finally:
            self.logger.info(
                f"Deployment completed in {job_result.duration}"
            )


jobs = [NewBranch]
register_jobs(*jobs)

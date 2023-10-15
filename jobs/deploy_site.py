"""Branch Job"""
from nautobot.extras.jobs import Job, StringVar
from nautobot.dcim.models import Location, LocationType

name = "Deployment Jobs"


class NewBranch(Job):
    """
    System job to deploy a new branch office """   
    site_name = StringVar(description="Name of the new site")

    class Meta:
        """Meta class."""
        name = "New Branch"
        description = "Provision a new branch site"
        has_sensitive_variables = False

    def run(self, site_name):
        """Execute Job."""

        job_result = self.job_result
        self.logger.info("Creating new branch office...")

        try:
            site = Location(
                name=site_name,
                location_type=LocationType.objects.filter(name="Site").get("id"),
                status="Active",
            )
            site.validated_save()
        finally:
            self.logger.info(
                f"Deployment completed in {job_result.duration}"
            )



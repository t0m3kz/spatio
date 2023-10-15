"""Branch Job"""
from nautobot.extras.jobs import Job, StringVar
from nautobot.dcim.models import Location, LocationType
from nautobot.extras.models import Status

name = "Deployment Jobs"


class NewBranch(Job):
    """
    System job to deploy a new branch office """   
    site_name = StringVar(description="Name of the new site")
    country_name = StringVar(description="Country of the new site")
    class Meta:
        """Meta class."""
        name = "New Branch"
        description = "Provision a new branch site"
        has_sensitive_variables = False

    def run(self, site_name, country_name):
        """Execute Job."""

        job_result = self.job_result
        self.logger.info("Creating new branch office...")

        try:
            self.logger.info(
                f"Adding Site {site_name}"
            )
            site = Location(
                name=site_name,
                location_type=LocationType.objects.filter(name="Site").get(),
                status=Status.objects.filter(name="Active").get(),
                parent=Location.objects.filter(name=country_name).get(),
            )
            site.validated_save()
        finally:
            self.logger.info(
                f"Deployment completed in {job_result.duration}"
            )


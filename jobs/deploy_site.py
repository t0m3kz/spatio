"""Branch Job"""
import os
from nautobot.extras.jobs import Job, StringVar
from nautobot.dcim.models import Location, LocationType
from nautobot.extras.models import Status

name = "Deployment Jobs"


class NewBranch(Job):
    """
    System job to deploy a new branch office """   
    site_name = StringVar(description="Name of the new site")
    city_name = StringVar(description="City of the new site")
    class Meta:
        """Meta class."""
        name = "New Branch"
        description = "Provision a new branch site"
        has_sensitive_variables = False

    def run(self, site_name, city_name):
        """Execute Job."""

        job_result = self.job_result
        self.logger.info("Creating new branch office...")
        github_pat = os.environ.get("NAUTOBOT_GITHUB_PAT")
        try:
            site = Location(
                name=site_name,
                location_type=LocationType.objects.filter(name="Site").get(),
                status=Status.objects.filter(name="Active").get(),
                parent=Location.objects.filter(name=city_name).get(),
            )
            site.validated_save()
            self.logger.info(
                f"Adding Site {site_name} in {city_name} to Nautobot {github_pat}"
            )
        finally:
            self.logger.info(
                f"Deployment completed in {job_result.duration}"
            )

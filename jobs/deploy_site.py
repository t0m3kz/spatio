"""Branch Job"""
import time
import datetime
import requests
from nautobot.extras.jobs import Job, StringVar
from nautobot.dcim.models import Location, LocationType
from nautobot.extras.models import Status

name = "Deployment Jobs"


class NewBranch(Job):
    """
    System job to deploy a new branch office"""

    site_name = StringVar(description="Name of the new site")
    city_name = StringVar(description="City of the new site")
    token = StringVar(description="Github Personal Access Token")

    class Meta:
        """Meta class."""

        name = "New Branch"
        description = "Provision a new branch site"
        has_sensitive_variables = False

    def run(self, site_name, city_name, token):
        """Execute Job."""

        job_result = self.job_result
        self.logger.info("Creating new branch office...")
        try:
            site = Location(
                name=site_name,
                location_type=LocationType.objects.filter(name="Site").get(),
                status=Status.objects.filter(name="Active").get(),
                parent=Location.objects.filter(name=city_name).get(),
            )
            site.validated_save()
            self.logger.info(f"Adding Site {site_name} in {city_name} to Nautobot")
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {token}",
            }

            # The data for the API request. This should match the inputs for your workflow.
            url = "https://api.github.com/repos/t0m3kz/spatio/actions/workflows/72607301/dispatches"
            data = {
                "ref": "main",
                "inputs": {"data": "deploy_branch"},
            }
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 204:
                self.logger.info(f"Site {site_name} in {city_name} is being deployed.")
                workflows_url = (
                    f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
                )
                # Let's wait a bit for the workflow to start
                time.sleep(2)
                # Wait until the workflow is completed
                start_time = datetime.datetime.now()
                while True:
                    response = requests.get(workflows_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        workflow = response.json()["workflow_runs"][0]
                        if workflow["conclusion"] is not None:
                            self.logger.info(
                                f"Deployment completed in {datetime.datetime.now() - start_time}"
                            )
                            break
                        else:
                            self.logger.info("Workflow still running. Waiting...")
                            print("Workflow still running. Waiting...")
                            time.sleep(5)
                    else:
                        print("Failed to get workflow status.")
                        break
            else:
                self.logger.error(
                    f"Site {site_name} in {city_name} cannot be deployed. {response.status_code}"
                )

        finally:
            self.logger.info(f"Deployment completed in {job_result.duration}")

import time
import datetime
import requests
from nautobot.extras.jobs import Job, StringVar, BooleanVar
from nautobot.dcim.models import Location, LocationType
from nautobot.extras.models import Status


class NewTenant(Job):
    """
    System job to deploy a new branch office
    """

    site_name = StringVar(description="Name of the new site")
    city_name = StringVar(description="City of the new site")
    token = StringVar(description="Github Personal Access Token")
    something = BooleanVar(description="Something")

    class Meta:
        """Meta class."""

        name = "New Branch"
        description = "Provision a new branch site"
        has_sensitive_variables = False
        approval_required = True

    def create_new_location(self, site_name, city_name):
        STATUS_PLANNED = Status.objects.get(name="Planned")
        site = Location(
            name=site_name,
            location_type=LocationType.objects.get(name="Site"),
            status=STATUS_PLANNED,
            parent=Location.objects.get(name=city_name),
        )
        site.validated_save()
        self.logger.info("Created new location %s", site)
        return site

    def trigger_workflow(self, token):
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}",
        }
        url = "https://api.github.com/repos/t0m3kz/spatio/actions/workflows/72607301/dispatches"
        data = {
            "ref": "main",
            "inputs": {"data": "deploy_branch"},
        }
        return requests.post(url, headers=headers, json=data, timeout=10)

    def wait_for_workflow_completion(self, token):
        workflows_url = "https://api.github.com/repos/t0m3kz/spatio/actions/runs"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}",
        }
        start_time = datetime.datetime.now()
        while True:
            response = requests.get(workflows_url, headers=headers, timeout=10)
            if response.status_code == 200:
                workflow = response.json()["workflow_runs"][0]
                if workflow["status"] == "queued":
                    self.logger.info("Workflow queued. Waiting...")
                    time.sleep(20)
                elif workflow["status"] == "in_progress":
                    self.logger.info("Workflow in progress. Waiting...")
                    time.sleep(20)
                elif (
                    workflow["conclusion"] == "success"
                    and workflow["status"] == "completed"
                ):
                    self.logger.info(
                        "Workflow completed in : %s",
                        datetime.datetime.now() - start_time,
                    )
                    break
                else:
                    self.logger.error("Workflow failed with %s", workflow["conclusion"])
                    raise Exception("Workflow failed.")
            else:
                self.logger.error("Failed to get workflow status.")
                raise ConnectionError("Failed to get workflow status.")

    def run(self, site_name, city_name, token):
        """Execute Job."""
        self.logger.info("Creating new branch office...")
        try:
            self.create_new_location(site_name, city_name)
            response = self.trigger_workflow(token)
            if response.status_code == 204:
                self.logger.info(
                    "Site %s in %s is being deployed.", site_name, city_name
                )
                time.sleep(2)
                self.wait_for_workflow_completion(token)
            else:
                self.logger.error(
                    "Site %s in %s cannot be deployed. Status code: %d",
                    site_name,
                    city_name,
                    response.status_code,
                )
        finally:
            self.logger.info("Deployment completed in %s", self.job_result.duration)

"""Branch Job"""
import time
import datetime
import requests
from nautobot.extras.jobs import Job, StringVar, ObjectVar
from nautobot.dcim.models import Location, LocationType
from nautobot.extras.models import Status

name = "ACI Jobs"


class NewBranch(Job):
    """
    System job to deploy a new branch office"""

    site_name = StringVar(description="Name of the new site")
    city_name = ObjectVar(
        model=Location,
        query_params={
            "location_type": "City"
        },
        display_field="name"
    )
    token = StringVar(description="Github Personal Access Token")

    class Meta:
        """Meta class."""

        name = "New Branch"
        description = "Provision a new branch site"
        has_sensitive_variables = False

    def __call__(self, *args, **kwargs):
        """Call the job."""
        return super().__call__(*args, **kwargs)

    def run(self, site_name, city_name, token):
        """Execute Job."""
        STATUS_PLANNED = Status.objects.get(name="Planned")
        job_result = self.job_result
        self.logger.info("Creating new branch office...")
        try:
            site = Location(
                name=site_name,
                location_type=LocationType.objects.get(name="Site"),
                status=STATUS_PLANNED,
                parent=Location.objects.get(name=city_name),
            )
            site.validated_save()
            self.logger.info("Created new location", extra={"object": site})
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
                    "https://api.github.com/repos/t0m3kz/spatio/actions/runs"
                )
                # Let's wait a bit for the workflow to start
                time.sleep(2)
                # Wait until the workflow is completed
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
                                "Workflow completed in : %s.",
                                datetime.datetime.now() - start_time,
                            )
                            break
                        else:
                            self.logger.error(
                                "Workflow failed with %s.", workflow["conclusion"]
                            )
                            raise Exception("Workflow failed.")
                    else:
                        self.logger.error("Failed to get workflow status.")
                        raise ConnectionError("Failed to get workflow status.")
            else:
                self.logger.error(
                    "Site %s in %s cannot be deployed. Status code: %d",
                    site_name,
                    city_name,
                    response.status_code,
                )

        finally:
            self.logger.info("Deployment completed in %s", job_result.duration)

    def push_to_repo(self):
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
            workflows_url = "https://api.github.com/repos/t0m3kz/spatio/actions/runs"
            # Let's wait a bit for the workflow to start
            time.sleep(2)
            # Wait until the workflow is completed
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
                            "Workflow completed in : %s.",
                            datetime.datetime.now() - start_time,
                        )
                        break
                    else:
                        self.logger.error(
                            "Workflow failed with %s.", workflow["conclusion"]
                        )
                        raise Exception("Workflow failed.")
                else:
                    self.logger.error("Failed to get workflow status.")
                    raise ConnectionError("Failed to get workflow status.")
        else:
            self.logger.error(
                "Site %s in %s cannot be deployed. Status code: %d",
                site_name,
                city_name,
                response.status_code,
            )

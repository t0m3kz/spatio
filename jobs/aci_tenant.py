"""Branch Job"""
import time
import datetime
import requests
from nautobot.extras.jobs import Job, StringVar, ObjectVar, ChoiceVar
from nautobot.dcim.models import Location
from nautobot.ipam.models import Namespace
from nautobot.extras.models import Tag, RelationshipAssociation, Relationship

name = "Cisco ACI Jobs"  # pylint: disable=invalid-name


class AciTenant(Job):
    """
    System job to deploy a new branch office
    """

    location = ObjectVar(
        model=Location,
        query_params={"location_type": "Site"},
        display_field="name"
    )

    ENVIRONMENTS = (
        ("LAB", "LAB"),
        ("PROD", "Production")
    )

    environment = ChoiceVar(choices=ENVIRONMENTS)

    tenant_name = StringVar(description="Name of the tenant")

    # CHOICES = (
    #     ("task1", "Deloyment Scenario 1"),
    #     ("task2", "Deloyment Scenario 2"),
    #     ("task3", "Deloyment Scenario 3"),
    #     ("task4", "Deloyment Scenario 4"),
    # )
    # deployment = ChoiceVar(choices=CHOICES)

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class."""

        name = "New Tenant"
        description = "Provision a new tenant"
        has_sensitive_variables = False
        approval_required = False

    def create_new_tenant(self, tenant_name, environment, site):
        """Create new tenant."""
        tenant = Namespace(
            name=f"{environment}_{site}_{tenant_name}",
            description=f"Tenant for {tenant_name}",
            location=Location.objects.get(name=site),
            _custom_field_data={
                "namespace_type": "Tenant",
                "namespace_config": {
                    "aci_name": tenant_name,
                    "environment": environment,
                    "site": site,
                    "role": "tenant",
                },
            },
            # source_ipam_namespace=Namespace.objects.get(name="Global"),
            # source_ipam_namespace=Namespace.objects.get(name="Global"),

            # source_for_associations=
            source_for_associations={
                "source_id": Namespace.objects.get(name="Global").id,
            }
        )
        tenant.tags.add(Tag.objects.get(name="ACI"))
        tenant.tags.add(Tag.objects.get(name=environment))
        # tenant.source_for_associations.add(source_id=Namespace.objects.get(name="Global").id)
        # tenant.source_for_associations.add(
        # tenant.source_for_associations.add(
        #     RelationshipAssociation.objects.create(
        #         source_type="Namespace",
        #         source_id=tenant.id,
        #         destination_type="Tenant",
        #         destination_id=tenant.id,
        #     )
        # )
        tenant.validated_save()
        # _relationship = RelationshipAssociation(
        #     source_type="ipam.namespace",
        #     source_id=Namespace.objects.get(name=f"{environment}_{site}_{tenant_name}").id,
        #     destination_type="ipam.namespace",
        #     destination_id=Namespace.objects.get(name="Global").id,
        #     relationship=Relationship.objects.get(label="Nested Namespaces"),
        # )
        # _relationship.validated_save()
        self.logger.info("Created new tenant %s", tenant_name)
        return tenant

    def run_workflow(self, token):
        """Run workflow and wait for result."""
        start_time = datetime.datetime.now()
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        url = (
            "https://github.developer.allianz.io/api/v3"
            "/repos/AGN/workflows/actions/workflows/aci.yaml/dispatches"
        )
        data = {"ref": "main", "inputs": {"data": "deploy_branch"}}
        result = requests.post(url, headers=headers, json=data, timeout=10)
        if result.status_code == 204:
            self.logger.info("Workflow dispatched.")
            time.sleep(2)
            workflows_url = (
                "https://github.developer.allianz.io/api/v3"
                "/repos/AGN/workflows/actions/workflows/aci.yaml/runs"
            )
            response = requests.get(workflows_url, headers=headers, timeout=10)
            if response.status_code == 200:
                url = response.json()["workflow_runs"][0]["url"]
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    while True:
                        workflow = requests.get(url, headers=headers, timeout=10).json()
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
                            self.logger.error(
                                "Workflow failed with %s", workflow["conclusion"]
                            )
                            raise RuntimeError("Workflow failed.")
                else:
                    self.logger.error("Failed to get workflow status.")
                    raise ConnectionError("Failed to get workflow status.")
            else:
                self.logger.error("Failed to get workflow run.")
                raise ConnectionError("Failed to get workflow run.")
        else:
            self.logger.error("Failed to dispatch workflow.")
            raise ConnectionError("Failed to dispatch workflow.")

    def run(self, **data):
        """Execute Job."""

        self.logger.info("Creating new tenant...")
        try:
            self.create_new_tenant(
                tenant_name=data["tenant_name"],
                environment=data["environment"],
                site=data["location"].name,
            )
            self.logger.info(
                "Tenant %s created with %s and %s ",
                data["tenant_name"],
                data["environment"],
                data["location"].name,
            )
            # self.run_workflow(token=os.getenv("GITHUB_TOKEN"))
        finally:
            self.logger.info("Deployment completed successfully.")

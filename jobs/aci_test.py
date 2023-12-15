"""Test Job"""
from nautobot.extras.jobs import Job, StringVar, MultiObjectVar, MultiChoiceVar
from nautobot.dcim.models import Location, Device


name = "Cisco ACI Jobs"  # pylint: disable=invalid-name


class AciTest(Job):
    """
    System job to deploy a new branch office
    """

    selected_sites = MultiObjectVar(
        model=Location, query_params={"location_type": "Site"}, display_field="name"
    )
    sites = [site.name for site in selected_sites]

    ENVIRONMENTS = (("LAB", "LAB"), ("PROD", "PRODUCTION"))

    environment = MultiChoiceVar(choices=ENVIRONMENTS)

    tenant_name = StringVar(description="Name of the tenant")

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class."""

        name = "Test"
        description = "Provision of test"
        has_sensitive_variables = False
        approval_required = False

    def run(self, **data):
        """Execute Job."""

        self.logger.info("Creating new test...")
        try:

            devices = Device.objects.filter(
                location__name__in=data["sites"],
                role__name="controller",
                platform__name="aci",
                name__contains="01",
                tags__name__in=data["environment"],
            )

            apics = [device.name for device in devices]

            self.logger.info(
                "Test %s created for %s in %s using %s",
                data["tenant_name"],
                data["environment"],
                data["sites"],
                apics,
            )
            # self.run_workflow(token=os.getenv("GITHUB_TOKEN"))
        finally:
            self.logger.info("Deployment completed successfully.")

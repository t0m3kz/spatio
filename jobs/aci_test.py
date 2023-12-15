"""Test Job"""
from django.contrib.contenttypes.models import ContentType
from nautobot.extras.jobs import Job, StringVar, MultiObjectVar, ChoiceVar
from nautobot.dcim.models import Location, Device
from nautobot.ipam.models import Namespace
from nautobot.extras.models import Tag, RelationshipAssociation, Relationship


name = "Cisco ACI Jobs"  # pylint: disable=invalid-name


class AciTest(Job):
    """
    System job to deploy a new branch office
    """

    sites = MultiObjectVar(
        model=Location, query_params={"location_type": "Site"}, display_field="name"
    )

    ENVIRONMENTS = (("LAB", "LAB"), ("PROD", "PRODUCTION"))

    environment = ChoiceVar(choices=ENVIRONMENTS)

    tenant_name = StringVar(description="Name of the tenant")

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class."""

        name = "Test"
        description = "Provision of test"
        has_sensitive_variables = False
        approval_required = False

    def create_new_tenant(self, tenant_name, environment, sites):
        """Create new tenant."""
        try:
            for site in sites:
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
                )
                self.logger.info(
                    "Creating new tenant %s on %s", tenant_name, environment
                )
                tenant.tags.add(Tag.objects.get(name="ACI"))
                tenant.tags.add(Tag.objects.get(name=environment))
                tenant.validated_save()
                parent_namespace = RelationshipAssociation(
                    source_type=ContentType.objects.get_for_model(Namespace),
                    source_id=Namespace.objects.get(
                        name=f"{environment}_{site}_{tenant_name}"
                    ).id,
                    destination_type=ContentType.objects.get_for_model(Namespace),
                    destination_id=Namespace.objects.get(name="Global").id,
                    relationship=Relationship.objects.get(label="Nested Namespaces"),
                )
                parent_namespace.validated_save()
            self.logger.info("Created new tenant %s in %s", tenant_name, sites)
        except Exception as err:
            self.logger.error("Failed to create in Nautobot new tenant %s", tenant_name)
            raise RuntimeError("Failed to create new tenant.") from err

    def run(self, **data): # pylint: disable=arguments-differ
        """Execute Job."""

        self.logger.info("Creating new test...")
        try:
            sites = [site.name for site in data["sites"]]
            devices = Device.objects.filter(
                location__name__in=sites,
                role__name="controller",
                platform__name="aci",
                name__contains="01",
                tags__name=data["environment"],
            )

            apics = [device.name for device in devices]

            self.logger.info(
                "Test %s created for %s in %s using %s",
                data["tenant_name"],
                data["environment"],
                sites,
                apics,
            )
            # self.run_workflow(token=os.getenv("GITHUB_TOKEN"))
        finally:
            self.logger.info("Deployment completed successfully.")

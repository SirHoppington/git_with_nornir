import argparse
from nornir import InitNornir
from nornir_salt.plugins.functions import FFun
from nornir.core.filter import F
from nornir.core.exceptions import NornirExecutionError
from nornir_napalm.plugins.tasks import napalm_configure
from nornir_utils.plugins.functions import print_result

from utilities.check_config_changes import compare_changes

new_config = "network-changes"
backup_dir = "config-backups"

# Create config parser to set dry_run when running script
parser = argparse.ArgumentParser()

parser.add_argument(
    "--dry_run", dest="dry", action="store_true", help="Will not run on devices"
)

parser.add_argument(
    "--no_dry_run", dest="dry", action="store_false", help="Will run on devices"
)

parser.set_defaults(dry=True)
args = parser.parse_args()

nr = InitNornir(config_file="config.yml")

# Deploy network configuration task to hosts
def deploy_network(task):
    """Configures network with NAPALM"""
    device = task.host.name
    print(f"Deploying to Device: {device}")
    task.run(
        name=f"Configuring {device}!",
        task=napalm_configure,
        filename=f"{new_config}/{device}.cfg",
        dry_run=args.dry,
        replace=False
    )


def main():
    crq_hosts = compare_changes(golden=backup_dir, proposed=new_config)
    filtered_hosts = FFun(nr, FL=crq_hosts)
    result = filtered_hosts.run(task=deploy_network)
    print_result(result)
    if result.failed:
        raise NornirExecutionError(result)


if __name__ == "__main__":
    main()
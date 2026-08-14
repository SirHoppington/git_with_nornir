"""Deploy pending change requests to the network with Nornir and NAPALM.

Change requests live in change-requests/<hostname>/<change-name>.cfg, so the
folder tells us the device and the filename is free to describe the change.

Requests are removed once they have been deployed, so anything still sat in
those folders is by definition pending - we just read the directory.
"""

import argparse
from pathlib import Path

from nornir import InitNornir
from nornir.core.exceptions import NornirExecutionError
from nornir_napalm.plugins.tasks import napalm_configure
from nornir_utils.plugins.functions import print_result

CHANGE_DIR = Path("change-requests")
REPORT_FILE = Path("diff.md")


def parse_args():
    parser = argparse.ArgumentParser(description="Deploy network change requests")
    parser.add_argument(
        "--dry_run", dest="dry", action="store_true", help="Will not run on devices"
    )
    parser.add_argument(
        "--no_dry_run", dest="dry", action="store_false", help="Will run on devices"
    )
    parser.set_defaults(dry=True)
    return parser.parse_args()


def find_changes():
    """Return {device: combined config} for every device with a pending change.

    A device with more than one pending change gets them joined together, so it
    only takes a single config session on the box.
    """
    changes = {}
    for folder in sorted(CHANGE_DIR.iterdir()):
        configs = [p.read_text().strip() for p in sorted(folder.glob("*.cfg"))]
        if configs:
            changes[folder.name] = "\n".join(configs)

    return changes


def deploy_network(task, changes, dry_run):
    """Configures network with NAPALM"""
    device = task.host.name
    print(f"Deploying to device: {device}")
    task.run(
        name=f"Configuring {device}!",
        task=napalm_configure,
        configuration=changes[device],
        dry_run=dry_run,
        replace=False,
    )


def write_report(result, dry_run):
    """Write the device generated diffs out as markdown for the PR comment."""
    heading = "Dry run - no changes applied" if dry_run else "Changes applied"
    report = [f"### {heading}\n"]

    for device, multi_result in result.items():
        if multi_result.failed:
            body = f"```\nFAILED: {multi_result[-1].exception}\n```"
        elif multi_result[1].diff:
            body = f"```diff\n{multi_result[1].diff}\n```"
        else:
            body = "_No changes - the device already matches this config_"

        report.append(f"**{device}**\n\n{body}\n")

    REPORT_FILE.write_text("\n".join(report))


def main():
    args = parse_args()

    changes = find_changes()
    if not changes:
        print("No change requests pending, nothing to do")
        REPORT_FILE.write_text("### No change requests to deploy\n")
        return

    nr = InitNornir(config_file="config.yml")

    # Nornir happily filters down to nothing and reports success, so check the
    # folder names against the inventory before we go anywhere near a device.
    unknown = sorted(set(changes) - set(nr.inventory.hosts))
    if unknown:
        raise SystemExit(f"Change requests for devices not in inventory: {unknown}")

    #devices = nr.filter(filter_func=lambda host: host.name in changes)
    devices = nr.filter(name__in=changes)
    
    print(f"{'Dry running' if args.dry else 'Deploying'} against: {', '.join(changes)}")

    result = devices.run(task=deploy_network, changes=changes, dry_run=args.dry)
    print_result(result)
    write_report(result, args.dry)

    if result.failed:
        raise NornirExecutionError(result)


if __name__ == "__main__":
    main()
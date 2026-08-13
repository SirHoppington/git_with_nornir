"""Deploy pending change requests to the network with Nornir and NAPALM.

Change requests live in change-requests/<hostname>/<change-name>.cfg. The device
is taken from the folder name, so the filename is free to describe the change.

The workflow passes in the files from the Git diff with --files, so only the
devices touched by a pull request get contacted. Run it with no arguments and it
picks up everything pending, which is handy for testing locally.
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
    parser.add_argument(
        "--files", default="", help="Space separated change request paths"
    )
    parser.set_defaults(dry=True)
    return parser.parse_args()


def find_changes(files):
    """Return {hostname: combined config} for every pending change request.

    Deleted files are skipped - they still show up in the Git diff, but there is
    nothing left to deploy. A device with more than one pending change gets them
    joined together, so it only takes one config session.
    """
    paths = CHANGE_DIR.rglob("*.cfg")
    
    if files:
        paths = [Path(f) for f in files.split()]

    changes = {}
    for path in sorted(paths):
        if not path.is_file():
            continue
        device = path.parent.name
        config = path.read_text().strip()
        changes[device] = f"{changes[device]}\n{config}" if device in changes else config

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
    lines = [f"### {heading}", ""]

    for device, multi_result in result.items():
        lines += [f"**{device}**", ""]

        if multi_result.failed:
            lines += ["```", f"FAILED: {multi_result[-1].exception}", "```", ""]
        elif multi_result[1].diff:
            lines += ["```diff", multi_result[1].diff, "```", ""]
        else:
            lines += ["_No changes - the device already matches this config_", ""]

    REPORT_FILE.write_text("\n".join(lines))


def main():
    args = parse_args()

    changes = find_changes(args.files)
    if not changes:
        print("No change requests pending, nothing to do")
        return

    nr = InitNornir(config_file="config.yml")
    devices = nr.filter(filter_func=lambda host: host.name in changes)

    # A typo in a folder name would otherwise leave us deploying to nothing at
    # all, and reporting success while we did it.
    missing = set(changes) - set(devices.inventory.hosts)
    if missing:
        raise SystemExit(f"Change requests for devices not in inventory: {sorted(missing)}")

    print(f"{'Dry running' if args.dry else 'Deploying'} against: {', '.join(changes)}")

    result = devices.run(task=deploy_network, changes=changes, dry_run=args.dry)
    print_result(result)
    write_report(result, args.dry)

    if result.failed:
        raise NornirExecutionError(result)


if __name__ == "__main__":
    main()
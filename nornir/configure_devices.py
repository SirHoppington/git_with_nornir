import argparse
from pathlib import Path

from nornir import InitNornir
from nornir.core.exceptions import NornirExecutionError
from nornir_napalm.plugins.tasks import napalm_configure
from nornir_utils.plugins.functions import print_result

CHANGE_DIR = Path("change-requests")
REPORT_FILE = Path("diff.md")


def parse_args():
    parser = argparse.ArgumentParser(description="Deploy change requests")

    parser.add_argument(
        "--dry_run", dest="dry", action="store_true", help="Will not run on devices"
    )
    parser.add_argument(
        "--no_dry_run", dest="dry", action="store_false", help="Will run on devices"
    )
    parser.set_defaults(dry=True)

    parser.add_argument(
        "--files",
        default="",
        help="Space separated change request paths, as given by paths-filter",
    )
    parser.add_argument(
        "--devices",
        default="",
        help="Comma separated hostnames, an alternative to --files",
    )

    return parser.parse_args()


def changed_devices(args):
    """Work out which devices have a pending change request."""
    if args.devices:
        names = [d.strip() for d in args.devices.split(",") if d.strip()]
    elif args.files:
        names = [Path(f).stem for f in args.files.split() if f.strip()]
    else:
        names = [path.stem for path in sorted(CHANGE_DIR.glob("*.cfg"))]

    # dict.fromkeys de-duplicates while keeping the original order. The is_file()
    # check drops any change request that was deleted in this PR - it will still
    # show up in the diff, but there is nothing left to deploy.
    return [name for name in dict.fromkeys(names) if (CHANGE_DIR / f"{name}.cfg").is_file()]


def select_hosts(nr, names):
    """Filter the inventory down to the devices we actually have changes for."""
    devices = nr.filter(filter_func=lambda host: host.name in set(names))

    missing = set(names) - set(devices.inventory.hosts)
    if missing:
        raise SystemExit(f"Change requests found for hosts not in inventory: {sorted(missing)}")

    return devices


def deploy_network(task, dry_run):
    """Configures network with NAPALM"""
    device = task.host.name
    print(f"Deploying to device: {device}")
    task.run(
        name=f"Configuring {device}!",
        task=napalm_configure,
        filename=f"{CHANGE_DIR}/{device}.cfg",
        dry_run=dry_run,
        replace=False,
    )


def write_report(result, dry_run):
    """Write the device generated diffs out as markdown for the PR comment."""
    heading = "Dry run - no changes applied" if dry_run else "Changes applied"
    lines = [f"### {heading}", ""]

    for host, multi_result in result.items():
        lines.append(f"**{host}**")
        lines.append("")

        if multi_result.failed:
            # index 1 is the napalm_configure subtask, index 0 is deploy_network
            error = multi_result[1].exception if len(multi_result) > 1 else multi_result[0].exception
            lines += ["```", f"FAILED: {error}", "```", ""]
            continue

        diff = multi_result[1].diff
        if diff:
            lines += ["```diff", diff, "```", ""]
        else:
            lines += ["_No changes - device already matches the requested config_", ""]

    REPORT_FILE.write_text("\n".join(lines))
    print(f"Wrote report to {REPORT_FILE}")


def main():
    args = parse_args()

    names = changed_devices(args)
    if not names:
        print("No change requests to deploy, nothing to do")
        return

    nr = InitNornir(config_file="config.yml")
    devices = select_hosts(nr, names)

    print(f"{'Dry running' if args.dry else 'Deploying'} against: {', '.join(names)}")

    result = devices.run(task=deploy_network, dry_run=args.dry)
    print_result(result)
    write_report(result, args.dry)

    if result.failed:
        raise NornirExecutionError(result)


if __name__ == "__main__":
    main()
import os
import filecmp


def compare_changes(golden, proposed):
    """Return hostnames where the golden and proposed configs differ."""
    print("Golden:", os.listdir(golden))
    print("Proposed:", os.listdir(proposed))

    files = os.listdir(golden)

    same, different, errors = filecmp.cmpfiles(
        golden,
        proposed,
        files,
        shallow=False,
    )

    hostnames = [
        os.path.splitext(filename)[0]
        for filename in different
    ]

    return hostnames


def main():
    golden = "golden"
    proposed = "change-requests"

    results = compare_changes(golden, proposed)

    print(f"Changed hosts: {results}")

if __name__ == "__main__":
    main()
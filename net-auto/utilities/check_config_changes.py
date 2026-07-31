import os
import filecmp


# Compare the files in crq_configs and snapshots/configs
def compare_changes():
    d1 = "./gold_config/"
    d2 = "./crq_configs/"
    files = []
    for file in os.listdir("./gold_config/"):
        files.append(file)
    results = filecmp.cmpfiles(d1, d2, files, shallow=True)
    hostnames = [os.path.splitext(x)[0] for x in results[1]]
    return hostnames


def main():
    compare_changes()


if __name__ == "__main__":
    main()
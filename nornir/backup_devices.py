# backup_devices.py

import os
from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
from nornir.core.filter import F

backup_dir="config-backups"

# Initiate Nornir object via config file
nr = InitNornir(config_file="config.yml")

# Function to create backup directory if it doesn't already exist
def create_backups_dir(backup_dir):
    os.makedirs(backup_dir, exist_ok=True)

# Function to save configuration to a txt file with hostname
def save_config_to_file(hostname, config):
    create_backups_dir(backup_dir)
    filename = f"{hostname}.cfg"
    with open(os.path.join(backup_dir, filename), "w") as f:
        f.write(config)
    print(f"Backed up {hostname} -> {os.path.join(backup_dir, filename)}")

# Use Napalm backup feature to retrieve backup for each device in a given group
def get_all_backups(environment):
    devices = nr.filter(F(groups__contains=environment))
    if not devices.inventory.hosts:
        raise ValueError(f"No hosts in group '{environment}'")
    
    backup_results = devices.run(task=napalm_get, getters=["config"])

    for host, multi_result in backup_results.items():
        if multi_result.failed:
            print(f"{host}: {multi_result[0].exception!r}")
        else:
            config = multi_result[0].result["config"]["running"]
            save_config_to_file(hostname=host, config=config)

# Function to update the golden config for devices within the "devices" Nornir object
def post_change_backup(task):
    backup_results = task.run(task=napalm_get, getters=["config"])
    for hostname in backup_results:
        config = backup_results[hostname][0].result["config"]["running"]
        save_config_to_file(hostname=hostname, config=config)
    return backup_results

def main():
    create_backups_dir(backup_dir)
    get_all_backups("dev")


if __name__ == "__main__":
    main()

import os
import shutil
from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get, napalm_cli
from nornir.core.filter import F
import datetime
import subprocess

GOLD_DIR = "gold_config"
CRQ_DIR = "crq_backups"

# Initiate Nornir object via config file
nr = InitNornir(config_file="./config.yaml")


# Function to create backup directory if it doesn't already exist
def create_backups_dir(backup_dir):
    try:
        if not os.path.exists(backup_dir):
            os.mkdir(backup_dir)
    except Exception as e:
        print(f"Error {e} for create_backups_dir")

# Function to save configuration to a txt file with hostname
def save_config_to_file(hostname, config, hash=None):
    try:
        if hash is not None:
            filename = f"{hostname}-{hash}.txt"
            BACKUP_DIR=f"{CRQ_DIR}/{hostname}"
        else:
            BACKUP_DIR=GOLD_DIR
            filename = f"{hostname}.txt"
        create_backups_dir(BACKUP_DIR)
        with open(os.path.join(BACKUP_DIR, filename), "w") as f:
            f.write(config)
    except Exception as e:
        print(f"Error {e} in save_config_to_file")



# Use Napalm backup feature to retrieve backup for IOS devices via specified env test/prod/etc
def get_all_backups(environment):
    try:
        prod_devices = nr.filter(F(groups__contains=environment))
        backup_results = prod_devices.run(task=napalm_get, getters=["config"])
        for hostname in backup_results:
            config = backup_results[hostname][0].result["config"]["running"]
            save_config_to_file(hostname=hostname, config=config)
        #shutil.copy(f"./gold_config/{hostname}.txt", f"./crq_configs/{hostname}.txt")
    except Exception as e:
        print(f"Error {e} for get_napalm_backups")

# Use Napalm backup feature to retrieve backup for IOS devices
def get_napalm_backups(task, hash=None):
    try:
        backup_result = task.run(task=napalm_get, getters=["config"])
        config = backup_result.result["config"]["running"]
        if hash is not None:
            hash = str(hash)
        save_config_to_file(hostname=task.host.name, config=config, hash=hash)
        #shutil.copy(f"./gold_config/{hostname}.txt", f"./crq_configs/{hostname}.txt")
        return config
    except Exception as e:
        print(f"Error {e} for get_napalm_backups")

# Function to update the golden config for devices within the "devices" Nornir object
def post_change_backup(task):
    backup_results = task.run(task=napalm_get, getters=["config"])
    for hostname in backup_results:
        config = backup_results[hostname][0].result["config"]["running"]
        save_config_to_file(hostname=hostname, config=config)
    return backup_results


# Manual alternative backup using napalm_cli to retrieve backup for IOS devices
# def get_napalm_backups():
#    backup_results = nr.run(task=napalm_cli, commands=["show running-config"])
#
#    for hostname in backup_results:
#        config = backup_results[hostname][0].result["show running-config"]
#        save_config_to_file(hostname=hostname, config=config)


def main():
    create_backups_dir()
    get_all_backups()


if __name__ == "__main__":
    main()
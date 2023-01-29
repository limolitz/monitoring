#!/usr/bin/env python3
import subprocess
import configparser
import json
from datetime import datetime, timezone
import time

def get_running_containers():
    containers = {}
    docker_curl = subprocess.Popen(["curl", "-o", "-", "-s", "-S", "--unix-socket", "/var/run/docker.sock", "http://localhost/containers/json"], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = docker_curl.communicate()
    if errors:
        print("Error", errors)
        exit(1)
    decoded = json.loads(output.decode('utf-8'))
    for container in decoded:
        if len(container['Names']) == 1:
            name = container['Names'][0][1:]
        else:
            # shortest name
            name = min(container['Names'], key=len)[1:]

        container_id = container['Id']
        state = container['State']
        status = container['Status']
        created = datetime.fromtimestamp(container['Created'], tz=timezone.utc).timestamp()
        image = container['Image']
        mounts = container['Mounts']
        containers[name] = {
            "id": container_id,
            "name": name,
            "state": state,
            "status": status,
            "created": created,
            "image": image
        }
    return containers


def get_single_container_info(container: dict):
    docker_curl = subprocess.Popen(["curl", "-o", "-", "-s", "-S", "--unix-socket", "/var/run/docker.sock", "http://localhost/containers/{}/json".format(container['id'])], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = docker_curl.communicate()
    if errors:
        print("Error", errors)
        exit(1)
    decoded = json.loads(output.decode('utf-8'))
    state = decoded['State']
    started_at = datetime.strptime(state['StartedAt'][:-4], "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)

    return {
        'started_at': started_at.timestamp(),
        'uptime': (datetime.now(timezone.utc) - started_at).total_seconds(),
    }


def get_single_container_stats(container: dict):
    docker_curl = subprocess.Popen(["curl", "-o", "-", "-s", "-S", "--unix-socket", "/var/run/docker.sock", "http://localhost/containers/{}/stats?stream=false".format(container['id'])], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = docker_curl.communicate()
    stats = {}
    if errors:
        print("Error", errors)
        exit(1)
    decoded = json.loads(output.decode('utf-8'))

    # TODO: get cpu

    # network stats
    if "networks" in decoded.keys():
        stats['interfaces'] = []
        for interface, value_dict in decoded["networks"].items():
            stats['interfaces'].append(interface)
            stats['{}_rx_bytes'.format(interface)] = value_dict["rx_bytes"]
            stats['{}_tx_bytes'.format(interface)] = value_dict["tx_bytes"]

    # memory stats
    try:
        stats["memory_usage"] = decoded["memory_stats"]["usage"]
    except KeyError:
        pass

    return stats


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')

    containers = get_running_containers()
    for name, container in containers.items():
        extra_info = get_single_container_info(container)
        for key, value in extra_info.items():
            if key in container.keys():
                print("Error: duplicate key {}".format(key))
                continue
            container[key] = value
        stats = get_single_container_stats(container)
        for key, value in stats.items():
            if key in container.keys():
                print("Error: duplicate key {}".format(key))
                continue
            container[key] = value
        mqttObject = {
            "topic": "docker_status",
            "measurements": container
        }

        json_object = json.dumps(mqttObject)
        print("Writing JSON: {}".format(json_object))

        sender = subprocess.Popen([config.get("Paths", "mqttPath")], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = sender.communicate(json_object.encode("utf-8"))
        print(output.decode("utf-8"), errors.decode("utf-8"))

        time.sleep(1)

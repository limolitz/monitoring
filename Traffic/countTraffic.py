#!/usr/bin/env python3
# log traffic on unix
import subprocess
import sys
import configparser
import json
import platform


def getAllInterfaces():
    ip = subprocess.Popen(["ip", "-json", "link", "show"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = ip.communicate()
    # no errors
    if len(errors) == 0:
        data = json.loads(output.decode("utf-8"))
        names = [entry["ifname"] for entry in data]
        return names
    else:
        # check if ip just doesn't support -json yet
        if "Option \"-json\" is unknown" in errors.decode("utf-8"):
            # fallback to plain output parsing
            # piping to grep
            # https://stackoverflow.com/questions/13332268/how-to-use-subprocess-command-with-pipes
            # grep output groups
            # https://unix.stackexchange.com/questions/13466/can-grep-output-only-specified-groupings-that-match
            ip = subprocess.Popen(["ip", "link", "show"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            grep = subprocess.Popen(
                ["grep", "-oP", "^[0-9]*: (\\K[a-z0-9]*)"],
                stdin=ip.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            ip.stdout.close()
            output, errors = grep.communicate()
            if errors:
                print(errors, file=sys.stderr)
            return output.decode("utf-8").splitlines()
        else:
            print(f"Error on ip call: {errors.decode('utf-8')}", file=sys.stderr)


def trafficInBytes(interface):
    if platform.system() == "Darwin":
        return trafficInBytesMac(interface)
    else:
        return trafficInBytesLinux(interface)


def trafficInBytesLinux(interface):
    bytes = []
    with open(f"/sys/class/net/{interface}/statistics/rx_bytes", "rb") as f:
        content = f.read()
        bytes.append(int(content))
    with open(f"/sys/class/net/{interface}/statistics/tx_bytes", "rb") as f:
        content = f.read()
        bytes.append(int(content))
    return bytes


def trafficInBytesMac(interface):
    netstat = subprocess.Popen(["netstat", "-b", "-n", "-I", interface], stdout=subprocess.PIPE)
    output, errors = netstat.communicate()
    # split by newlines
    lines = output.decode("utf-8").split('\n')
    # remove empty entries
    parts = list(filter(None, lines[1].split(" ")))
    ibytes = parts[6]
    obytes = parts[9]
    bytes = [ibytes, obytes]
    return bytes


def uptimeInSeconds():
    # get uptime in seconds
    uptime = int(subprocess.Popen("./getUptimeSeconds.sh", stdout=subprocess.PIPE).stdout.read())
    print(f'Uptime: {uptime}s')
    return uptime


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')

    interfaces = getAllInterfaces()
    if interfaces is None:
        print("Error on getAllInterfaces.", file=sys.stderr)
        exit(1)
    for interface in interfaces:

        uptime = uptimeInSeconds()
        traffic = trafficInBytes(interface)
        mqttObject = {
            "topic": "traffic",
            "name": interface,
            "measurements": {
                "uptime": uptime,
                f"{interface}_rx_bytes": int(traffic[0]),
                f"{interface}_tx_bytes": int(traffic[1])
            }
        }
        jsonObject = json.dumps(mqttObject)
        print(f"Writing JSON: {jsonObject}")
        sender = subprocess.Popen(
            [config.get("Paths", "mqttPath")],
            stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output, errors = sender.communicate(jsonObject.encode("utf-8"))
        print(output.decode("utf-8"))
        if errors:
            print(errors.decode("utf-8"), file=sys.stderr)

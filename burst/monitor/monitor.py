#!/usr/bin/env python3
import os, sys, json, time, subprocess, datetime, argparse
from burst.lcloud import *
from pprint import pprint

def stop_instance_by_url(url, conf):
    print ("STOP instance with public IP", url)
    # print ("DEBUG", os.path.abspath('.'), conf.secret)
    node = get_server(url=url, conf=conf)
    if not node:
        print ("No active instance found for IP", url)
    else:
        print ("shutting down node %s" % node)
        stop_server(node)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--ip",         required=True)
parser.add_argument("--provider",   required=True)
parser.add_argument("--access",     required=True)
parser.add_argument("--secret",     required=True)
parser.add_argument("--region",     required=True)
parser.add_argument("--project",    default="")
args = parser.parse_args()

while True:
    proc = subprocess.Popen(["docker", "ps", "--format='{{json .}}'"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    count  = 0
    now = datetime.datetime.utcnow()
    lines = proc.stdout.read().strip().split(b"\n")
    shuttime = 0
    for out in lines:
        out = out.decode().strip()[1:-1] #seems a docker bug; returning single-quoted json blob
        # print("OUT:", out)
        if not out:
            continue
        j = json.loads(out)
        # pprint(j)
        # print ("RUNNING:", j['Image'], j['Labels'])
        for x in j['Labels'].split(','):
            if 'burstable' in x:
                key, val = x.split('=')
                # print ("LABEL: %s = %s" % (key, val))
                if key == 'ai.burstable.shutdown':
                    delay = int(val)
                    t = now + datetime.timedelta(seconds = delay)
                    if shuttime < t:
                        shuttime = t
                else:
                    print ("ERROR -- unknown docker label %s=%s" % (key, val))
                    sys.stdout.flush()
            count += 1

    remain = (shuttime-now).total_seconds() if shuttime else 3600
    print ("time now:", now, "shutoff time:", shuttime, "remaining:", remain)
    sys.stdout.flush()
    if remain and remain < datetime.timedelta(seconds=0):
        print ("Proceeding to shutdown {0}".format(args.ip))
        sys.stdout.flush()
        stop_instance_by_url(args.ip, vars(args))
        break

    time.sleep(5)

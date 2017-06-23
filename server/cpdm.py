#!/usr/bin/env python
import ConfigParser
import json
import logging
import os
import time
from datetime import date
import rabbitmqSend as RmqSend

import sys
import stat
import cloudstackApi as CSApi
import uuid
from shutil import copy2
import argparse

import ntpath


def mainFlow(seeds_file,networkfile):
    """
    Main execution workflow
    :return:
    """

    # Read configuration file
    config = ConfigParser.ConfigParser()
    scriptPath = os.path.abspath(os.path.join(os.path.realpath(__file__), os.pardir))
    config.read('{}/cpdm.ini'.format(scriptPath))
    #init logging
    todaystr = date.today().strftime("%Y%m%d")
    logging.basicConfig(filename="{}CPDM_{}.log".format(config.get("general", "logpath"), todaystr),
                        level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    #step 1: Read input and create random unique id

    #Generate Job ID
    jobid = str(uuid.uuid1())

    #create directory for jobs files
    data_directory = "{}/{}".format(config.get("general", "nfspath"),jobid)
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
    os.chmod(data_directory, stat.S_IRWXU | stat.S_IRWXO | stat.S_IRWXG)
    #Read input seeds
    with open(seeds_file) as f:
        seed_proteins = map(int, f.readline().rstrip().split(','))

    #copy network input to job directory
    copy2(networkfile, data_directory)

    #step 2: count input seeds and find service offering
    count_seeds_proteings = len(seed_proteins)  # metrame ta orismata tou seeds.txt gia to analogo offering
    if count_seeds_proteings >= 0 and count_seeds_proteings < 10:
        vm_service_offering = "bikos_3cpu"
    elif count_seeds_proteings >= 10 and count_seeds_proteings < 25:
        vm_service_offering = "bikos_5cpu"
    else:
        vm_service_offering = "bikos_10cpu"

    #step 3: Add job to queue
    message = {
            "jobid": jobid,
            "seed_proteins": seed_proteins,
            "networkfile": ntpath.basename(networkfile)
        }

    queue_result = RmqSend.sendMessageToQueue(json.dumps(message),config)
    if queue_result == False:
        print "Problem in adding job to queue. Please look at log files for more information"
        sys.exit()
    else:
        print "A message with job details added to queue. JobID: {}. seed_proteins: {} and networkfile: {}".format(message["jobid"],message["seed_proteins"],message["networkfile"])


    #step 4: deploy new VM
    newvm = CSApi.deployVM("cpdm-{}".format(jobid),config.get("taskmanager", vm_service_offering),config)
    if newvm != False:
        print "A new VM with ID: {} has been deployed".format(newvm['deployvirtualmachineresponse']['id'])
    else:
        print "Problem in deployment VM. Please look at log files for more information"
        sys.exit()

    #step 5: wait until the problem is solved
    start = time.time()
    flag_job_running = True
    output_file = "{}/out.json".format(data_directory)
    print "Execute process. This will take a while. Please Wait..."
    while(flag_job_running):
        if os.path.exists(output_file):
            flag_job_running = False
        time.sleep(1)
    #read result
    with open(output_file,"r") as of:
        process_result = json.load(of)


    print "Analysis was finished in {} secs".format(time.time()-start)
    print "Results: "
    for protein in process_result:
        print "Seed Protein: {}, Number of neighbours: {}, subgraph: {}".format(protein['protein'],protein['neighbours'],protein['subgraph'])

    #step 6: destroy VM
    destroyVM = CSApi.destroyVM(newvm['deployvirtualmachineresponse']['id'], True, config)
    if destroyVM != False:
        print "A new VM with ID: {} has been set for destruction".format(newvm['deployvirtualmachineresponse']['id'])
    else:
        print "Problem in destroying VM. Please look at log files for more information"
        sys.exit()

    sys.exit()

if __name__ == '__main__':
    #set arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('seeds_file', action="store")
    parser.add_argument('network_file', action="store")

    options = parser.parse_args()
    mainFlow(options.seeds_file,options.network_file)

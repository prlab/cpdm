import ConfigParser
import json
import logging
from datetime import date
import pika

import sys

import cpdm_client_functions as CCF
import multiprocessing
import scipy.io as sio
import os
from functools import partial


#global config
config = ConfigParser.ConfigParser()
# Read configuration file
scriptPath = os.path.abspath(os.path.join(os.path.realpath(__file__), os.pardir))
config.read('{}/cpdm_client.ini'.format(scriptPath))
#init logging
todaystr = date.today().strftime("%Y%m%d")
logging.basicConfig(filename="{}/CPDMCLIENT_{}.log".format(config.get("general", "nfspath"), todaystr),
                        level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

def startnewanalysis(ch, method, properties, body):


    data = json.loads(body)
    logging.info("{}\tA new job arrived".format(data['jobid']))

    seeds_proteins = data['seed_proteins']
    seeds_number = len(seeds_proteins)

    #calculate number of processes
    processes_number = (multiprocessing.cpu_count()-1)
    if processes_number >= seeds_number:
        processes_number = seeds_number

    #load network
    network_path = "{}/{}/{}".format(config.get("general", "nfspath"),data['jobid'],data['networkfile'])
    if not os.path.exists(network_path):
        logging.error("The network file doesn't exists")
        sys.exit()

    network_data = sio.loadmat(network_path)

    logging.info("{}\tA new job is starting. We will process {} seed proteins at {} parallel processes".format(data['jobid'],seeds_number,processes_number))
    #start parallel analysis
    pool = multiprocessing.Pool(processes_number)
    func = partial(CCF.DMSP_new, parameters=[0.45, 0.75, 0.9, 2, network_path])

    print type(seeds_proteins)
    try:	
        results = pool.map(func, seeds_proteins, chunksize=(seeds_number // processes_number))   
    except:
        logging.exception('pool.map')
        sys.exit()

    output = [result[0] for result in results]
    seeds = [result[1] for result in results]
    starts = [result[2] for result in results]

    results_array = []

    for i in range(len(seeds_proteins)):
        results_seed = {
            'protein': seeds[i],
            'neighbours': starts[i],
            'subgraph': output[i]
        }
        results_array.append(results_seed)

    output_path = "{}/{}/out.json".format(config.get("general", "nfspath"),data['jobid'])

    with open(output_path,"w") as output_file:
        json.dump(results_array,output_file)

    logging.info("{}\tJob finished".format(data['jobid']))
    sys.exit()



def init():
    """
    Initialize config parser, logging and start queue consuming
    :return:
    """
    # Connect to Rabbit Mq and listen
    credentials = pika.PlainCredentials(config.get("general", "rabbitmquser"), config.get("general", "rabbitmqpwd"))
    parameters = pika.ConnectionParameters(config.get("general", "rabbitmqip"),
                                           5672,
                                           '/',
                                           credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=config.get("general", "rabbitmqqueue"))

    channel.basic_consume(startnewanalysis,
                          queue=config.get("general", "rabbitmqqueue"),
                          no_ack=True)
    channel.start_consuming()


if __name__=='__main__':
    init()

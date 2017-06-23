import pika
import ConfigParser
import logging
from datetime import date


def sendMessageToQueue(message, config):
    try:
        credentials = pika.PlainCredentials(config.get("general", "rabbitmquser"), config.get("general", "rabbitmqpwd"))
        parameters = pika.ConnectionParameters(config.get("general", "rabbitmqip"),
                                               5672,
                                               '/',
                                               credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=config.get("general", "rabbitmqqueue"))
        channel.basic_publish(exchange='',
                              routing_key=config.get("general", "rabbitmqqueue"),
                              body=message)
        connection.close()
        logging.info("Message has been send to the queue")
    except:
        logging.exception('Error in calling sendMessageToQueue method')
        return False
    return True



if __name__ == '__main__':
    # Read configuration file
    config = ConfigParser.ConfigParser()
    config.read('cpdm.ini')
    #init logging
    todaystr = date.today().strftime("%Y%m%d")
    logging.basicConfig(filename="{}rabbitmqSend_{}.log".format(config.get("general", "logpath"), todaystr),
                        level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    sendmsg = sendMessageToQueue('{"seed_proteins": [15, 26, 37, 85, 54, 82, 1243, 81, 256, 1321, 82, 1001, 52, 4, 13, 34, 145, 569, 1589, 25], "networkfile": "w.mat", "jobid": "568c476e-5736-11e7-877f-080027d12373"}',config)

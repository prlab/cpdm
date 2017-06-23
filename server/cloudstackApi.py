#!/usr/bin/env python
import ConfigParser
import base64
import hashlib
import hmac
import json
import logging
import time
import urllib
import urllib2
from datetime import date


def makeCloudstackRequest(requests, config):
    """
    Creates and executes a API request to Cloudstack
    :param requests: Key-Value object with request's paramaters
    :param config: python config object
    :return: repsonse from Cloudstack in json format
    """
    try:
        request = zip(requests.keys(), requests.values())  # Enwsi Keys kai Values
        request.sort(key=lambda x: str.lower(x[0]))
        requestUrl = "&".join(["=".join([r[0], urllib.quote_plus(str(r[1]))]) for r in
                               request])  # ftiaxnei URL gia to Request me ta Keys kai Values
        hashStr = "&".join(
            ["=".join([str.lower(r[0]), str.lower(urllib.quote_plus(str(r[1]))).replace("+", "%20")]) for r in request])
        sig = urllib.quote_plus(base64.encodestring(
            hmac.new(config.get('taskmanager', 'cloudstacksecretKey'), hashStr, hashlib.sha1).digest()).strip())
        requestUrl = config.get('taskmanager', 'cloudstackAPIurl') + requestUrl + "&signature=%s" % sig
        logging.info('Request for Cloudstack: url = {}'.format(requestUrl))
        response = urllib2.urlopen(requestUrl).read()
        logging.info("Success response from makeCloudstackRequest method")
        return response
    except:
        logging.exception('Error in calling makeCloudstackRequest method')
        return False


def getVMs(config):
    """
    Return the list of all VMs in the cloudstack
    :param config: python config object
    :return: Return array with state, id and ip of the VMs
    """

    # create empty array for vm's state and
    vm_ret = []
    try:
        # wait until all VM get started get info from cloudstack
        time.sleep(10)
        requests = {
            "apiKey": config.get("taskmanager", "cloudstackAPIkey"),
            "response": "json",
            "command": "listVirtualMachines",
            "listall": "true",
        }
        listvm = makeCloudstackRequest(requests,config)  # call main for new request
        if listvm == False:
            logging.error('Error in getVMs method. makeCloudstackRequest returned false')
            return vm_ret
        else:
            vmdata = json.loads(listvm)  # takes data from json results(state and ip address)
            vms = vmdata["listvirtualmachinesresponse"]["virtualmachine"]
            # get states for each new deploed vm
            for j in range(len(vms)):
                vm_i = {
                    "state": vms[j]["state"],
                    "id": vms[j]["id"],
                    "ip": vms[j]["nic"][0]["ipaddress"],
                }
                vm_ret.append(vm_i)
    except:
        logging.exception('Error in calling getVMs method')

    return vm_ret

def deployVM(vmname, serviceofferingid,config):
    """
    Create/Deploy a new VM
    :param vmname: the name of the VM
    :param serviceofferingid: uid of service offering of the new VM
    :param config: python config object
    :return: The data object with the details of the new VM
    """
    try:
        logging.info("Try to deploy VM with name: {} and offering: {}".format(vmname, serviceofferingid))
        request = {
            "apiKey": config.get("taskmanager", "cloudstackAPIkey"),
            "response": "json",
            "command": "deployVirtualMachine",
            "serviceofferingid": serviceofferingid,
            "templateid": config.get("taskmanager", "bikostemplate"),
            "zoneid": config.get("taskmanager", "cloudstackZoneID"),
            "domainid": config.get("taskmanager", "cloudstackDomainID"),
            "networkids": config.get("taskmanager", "cloudstackNetworkID"),
            "diskofferingid": config.get("taskmanager", "smalldiskoffer"),
            "displayname": vmname,
            "name": vmname
        }
        newvm = makeCloudstackRequest(request,config);
        if newvm == False:
            logging.error('Error in deployVM method. makeCloudstackRequest returned false')
            return False
        else:
            data = json.loads(newvm)
            return data
    except:
        logging.exception('Error in calling deployVM method')
        return False

def destroyVM(vmid, expunge,config):
    """
    Send request for destroying a VM
    :param vmid: the uid of the VM
    :param expunge: True or False if we want to expunge the VM
    :param config: python config object
    :return: The result of the request
    """
    try:
        request = {
            "apiKey": config.get("taskmanager", "cloudstackAPIkey"),
            "response": "json",
            "command": "destroyVirtualMachine",
            "id": vmid,
            "expunge": expunge
        }

        des = makeCloudstackRequest(request,config);
        if des == False:
            logging.error('Error in destroyVM method. makeCloudstackRequest returned false')
        else:
            return des
    except:
        return False


if __name__ == '__main__':
    # Read configuration file
    config = ConfigParser.ConfigParser()
    config.read('cpdm.ini')
    #init logging
    todaystr = date.today().strftime("%Y%m%d")
    logging.basicConfig(filename="{}cloudstackAPI_{}.log".format(config.get("general", "logpath"), todaystr),
                        level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    newvm = deployVM("ceidVM5", config.get("taskmanager", "bikos_3cpu"), config)
    print newvm

    print getVMs(config)

    if newvm != False:
        destroyVM(newvm['deployvirtualmachineresponse']['id'],True,config)
    print getVMs(config)







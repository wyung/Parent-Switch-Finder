#!/usr/bin/env python
"""
This script finds all running switches in the 10.11.12.xxx range and then
queries them to find all the macaddresses on them.
After filtering out uplink and downstream ports, it logs all the mac addresses
and ports remaining to a csv file

csv format is: switch_last_octect,port,mac

INSTALL:
depends on snimpy and right MIBS
on debian/ubuntu:
apt-get install snimpy
apt-get install snmp-mibs-downloader

picked switch list ommited for privacy
"""

import sys
pickled = True


if (pickled):   # Picked input
    import pickle
    mp = pickle.load(open('switches.pickle', 'r'))
    # only needed 
    switches = []
    for switchIp in mp.keys():
        if mp[switchIp]:
            switches.append( mp[switchIp][0])

else:
    import os
    import time
    from snimpy.manager import Manager as M
    from snimpy.manager import load

    load("BRIDGE-MIB")

    def find_switches():
        """ find all the switches in the 10.11.12.xxx range """
        sw = dict() # key/value = ip/mac of all the switches alive at the time of scan
        print "Scanning 10.11.12.xxx range..."
        for num in range(130,254): #start from 130 as we don't have switches lower than that
            ip = "10.11.12." + str(num)
            if os.system("ping -c 1 -w2 -t2 " + ip + " > /dev/null 2>&1") == 0: #host is alive!
                print "%s added to the list" % ip
                sw[ip] = ""
            else:
                print "%s is down" % ip
        return sw

    mp = dict() # key/value = ip of switch / tuple(switch port/macs on that port)
    cantquery = [] # list of switches that did not respond to snmp

    switches = find_switches()
    # DEBUG
    # uncomment line below to override switches to speed up testing
    # switches = {'10.11.12.161':'', '10.11.12.153':''}
    # query all the switches to retrieve mac addresses list
    for ip in switches.keys():
        print "Connecting to %s..." % ip
        try:
            c = M(host=ip, community="public", version=2, timeout=2, retries=1)
            # get the mac of the switch I'm connected to
            switches[ip] = str(c.dot1dBaseBridgeAddress)
            mp[ip] = dict() # return a list of tuples mac / port (not sorted!)
            for mpm,mpp in c.dot1dTpFdbPort.items():
                mac = str(mpm)
                port = int(mpp)
                if port not in mp[ip].keys(): # initiatilize the array for that port
                    mp[ip][port] = []
                mp[ip][port].append(mac)
        except:
            cantquery.append(ip)
            pass

    print "All these switches could not be queried (unreachable or unsupported MIBs): %s" % (cantquery)

# switches is seperate dictionary that contains ip/mac address 


# mp.keys()     ip of all switches
# mp[ip of switch].keys() Port #
# port address 0 is self
# mp[ip of switch].keys() Mac Address on that port#



huntTarget = sys.argv[1]
if (len(huntTarget) != 17):
    print("Mac Address of length != 17 entered, maybe you forgot the \":\"s?")
pos = [0,3,6,9,12,15]
stripped = ""
for b in pos:
    val = int (huntTarget[b:b+2],16)
    if (val < 10):
        stripped += str(int(huntTarget[b:b+2],0))
    else:
        stripped += huntTarget[b:b+2]
    if (b != 15):
        stripped += ':'
huntTarget = stripped

for switchIp in mp.keys():
    if (bool(mp[switchIp])):
        clear2del = True
        for port in mp[switchIp].keys():
            if huntTarget in mp[switchIp][port]:
                clear2del = False
                for sw in switches:
                    if ''.join(sw) in mp[switchIp][port]:
                        clear2del = True
        if (clear2del):
            del mp[switchIp]

print "Number of schrodinger parent switches: " + str(len(mp.keys()))
for switchIp in mp.keys():
    if (bool(mp[switchIp])):
        print huntTarget + ", I '" + switchIp + "' may be your father!"
# FILTERING IS BROKEN
# filter uplink and downlink ports
"""
for sw_ip, sw_mac in switches.iteritems():
    for p in mp[sw_ip].keys(): #need to look to othger switches, not my own!!
        if sw_mac in mp[sw_ip][p]:
            del mp[sw_ip][p]
"""

# log = open('dump-sws-macs-log-%s.csv' % time.strftime("%Y%m%d-%H%M%S"), 'w')
# for ip,pms in mp.iteritems(): #cycle over all switches
#     for p,ms in pms.iteritems(): #cycle over all port/mac dict items
#         for m in ms:
#             log.write("%s,%s,%s\n" % (ip.split(".",4)[-1],p,m))
# log.write("Failed (unreachable or unsupported MIBs): %s" % (cantquery))
# log.close()

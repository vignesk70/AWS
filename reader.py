import json
import os
import glob
import time

BOLT_URL = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "asdfgh123" # better to read from an environment variable
DBNAME = "demodb"
BOLT_GRAPHENE = "bolt://hobby-gcbfnjjgbjfigbkeckdlcgdl.dbs.graphenedb.com:24787"
GRAPHENE_USER = "democyrus"
GRAPHENE_PASSWORD = "b.oYbLGifSOZFj.E6T2CN4uFTt2xX7Y"

from py2neo import Graph,Node, Relationship

def patch_encryption():
        # Work around bug in py2neo
        from neobolt import security
        if not getattr(security.SecurityPlan.build, 'patched', None):
            old_build = security.SecurityPlan.build
            def build_encrypted(**config):
                config['encrypted'] = 1
                return old_build(**config)
            security.SecurityPlan.build = build_encrypted
            security.SecurityPlan.build.patched = True


def printlist(obj):
    for x in obj:
        #print(obj)
        print(x)


#
graph = Graph( BOLT_URL, auth=(USER, PASSWORD))
#graphene
# patch_encryption()
# graph = Graph( BOLT_GRAPHENE, auth=(GRAPHENE_USER, GRAPHENE_PASSWORD))

instanceip=set()
t = time.process_time()
print("Start processing server list")

path = 'cloudserver/NETSTAT/'
with open(path+'lightsail-merge.json') as json_file:
    data = json.load(json_file)
    i=1
    #print(len(data))
    for x in data:
        i=1
        for p in x['instances']:
            #print(i)

            # print("\nName:{}".format(p['name']))
            # print("Location:{}".format(p['location']['availabilityZone']))
            # print("Cpu:{}".format(p['hardware']['cpuCount']))
            # if p['publicIpAddress']:
            #     print(p['publicIpAddress'])
            try:
                p['publicIpAddress']
                # print('PublicIP: {}'.format( p['publicIpAddress']))
                instanceip.add(p['publicIpAddress'])
            except Exception as e:
                # print('No public ip')
                p['publicIpAddress']="No public ip"
            try:
                p['privateIpAddress']
                # print('PrivateIp: {}'.format(p['privateIpAddress']))
                instanceip.add(p['privateIpAddress'])

            except Exception as e:
                # print('No privateIpAddress ip')
                p['privateIpAddress']="No private ip"

            # print('availabilityZone: {}'.format(p['location']['availabilityZone']))
            # print('regionName: {}'.format( p['location']['regionName']))

            location = Node("Location",availabilityZone=p['location']['availabilityZone'],regionName=p['location']['regionName'])
            instance = Node("Instances",name=p['name'], privateIpAddress=p['privateIpAddress'],publicIpAddress=p['publicIpAddress'],
                stateCode=p['state']['code'],stateName=p['state']['name'])
            loc_ins = Relationship(location,"HOSTS",instance)
            graph.merge(location,"Location","availabilityZone")
            graph.merge(instance,"Instances","name")
            #print('nodecreated')
            graph.merge(loc_ins)
            #print('rel created')

            # printlist(p['hardware']['disks'])
            # printlist(p['networking']['ports'])

            #print("Network:{}".format(p['networking']['ports']))
            # netcount=1
            # for net in p['networking']['ports']:
            #     print("Network",type(net))
            #     print("Port {}\n {}".format(netcount, net))
            #     netcount+=1
            # i+=1
# print(instanceip)
print("Elapsed time ",(time.process_time()-t))
path2 = 'cloudserver/NETSTAT/merged'
#
# files = glob.glob(path+'*')
# for f in files:
# 	#print(f)
# 	with open(f) as json_file:
# 		data = json.load(json_file)
# 		print("Processing file for netstat -- ",f)
# 		for x in data:
# 			for z in x:
# 				for p in z['netstat']:
# 					if p['State']=='ESTABLISHED' and (p['Foreign Address'].find('127.0.0.1')==-1):
# 						print('Source {}->Destination {}'.format(p['Local Address'],p['Foreign Address']))
# 					else:
# 						pass
PORT_LIST=['80','443','3306']

def get_listening_ports(data,serverip):
    listen_ports=[]
    for x in data:
        for z in x:
            if z['serverIP']==serverip:
                for p in z['netstat']:

                    if p['State']=='LISTEN' and (p['Local Address'].find('0.0.0.0') or p['Local Address'].find('127.0.0.1')):
                        #print(p['Local Address'].split(':')[1])
                        listen_ports.append(p['Local Address'].split(':')[1])
    return listen_ports

t=time.process_time()
print("Processing netstat data")
files = glob.glob(path2+'*')
for f in files:
    with open(f) as json_file:
        print("Processing file for netstat -- ",f)
        data = json.load(json_file)
        for x in data:
            for z in x:
                # print('Serverip', z['serverIP'])

                listen_ports=get_listening_ports(data,z['serverIP'])
                # print(listen_ports)

                for p in z['netstat']:
                    if p['State']=='ESTABLISHED' and (p['Foreign Address'].find('127.0.0.1')==-1):
                        localip = p['Local Address'].split(":")[0]
                        localport=p['Local Address'].split(":")[1]
                        foreignip=p['Foreign Address'].split(":")[0]
                        foreignport=p['Foreign Address'].split(":")[1]
                        if (localport in PORT_LIST) or (foreignport in PORT_LIST) :
                            # print('Localip {} {} -> Foreignip {} {}'.format(localip,localport,foreignip,foreignport))
                            if (localport in listen_ports) and (localip in instanceip):
                                # print('match instance and set as destination',localport)
                                destination = graph.nodes.match("Instances",privateIpAddress=localip).first()
                                # print(destination)
                                source = graph.nodes.match("Instances",publicIpAddress=foreignip).first()
                                if source:
                                    # print('available')
                                    pass
                                else:
                                    source = Node("External",publicIpAddress=foreignip)
                                rel = "PORT_"+localport
                                src_dest = Relationship(source,rel,destination)
                                graph.merge(source,"External","publicIpAddress")
                                graph.merge(destination,"Instances","name")
                                graph.merge(src_dest)
                                # instance = Node("Instances",name=p['name'], privateIpAddress=p['privateIpAddress'],publicIpAddress=p['publicIpAddress'])
                                # loc_ins = Relationship(location,"HOSTS",instance)
                                # graph.merge(location,"Location","availabilityZone")
                                # graph.merge(instance,"Instances","name")
                                # #print('nodecreated')
                                # graph.merge(loc_ins)
                            if not (localport in listen_ports) and (localip in instanceip):
                                # print("match instance and set as source", foreignport)
                                source = graph.nodes.match("Instances",privateIpAddress=localip).first()
                                # print(source)
                                destination = graph.nodes.match("Instances",publicIpAddress=foreignip).first()
                                # print(destination)
                                if destination:
                                    # print('available')
                                    pass
                                else:
                                    destination = Node("External",publicIpAddress=foreignip)
                                    # print('NA')
                                rel = "PORT_"+foreignport
                                src_dest = Relationship(source,rel,destination)
                                graph.merge(destination,"External","publicIpAddress")
                                graph.merge(source,"Instances","name")
                                graph.merge(src_dest)

print("Elapsed time ",time.process_time()-t)

import requests,json,csv,getpass,code
#todo - Verify that servers that are grouped together behind one VS are not grouped with different servers behind other VSs
#code.interact(local=dict(globals(),**locals()))



def ns_login():
    global ns_user,ns_server,ns_creds
    ns_server = input('Server fqdn:port : ')
    ns_user = input('Username : ')
    ns_pass = getpass.getpass('Password : ')
    ns_creds = {'X-NITRO-User': ns_user, 'X-NITRO-PASS':ns_pass}
    #return ns_server,ns_creds


#get a list of raw information on all VSs
def get_vs():
    url =  'http://' + ns_server + '/nitro/v1/config/lbvserver/'
    headers = ns_creds
    r = requests.get(url,headers=headers,verify=False)
    r = json.loads(r.text)
    virtualserver_list = r['lbvserver']
    return virtualserver_list


#extract the name of all VSs from the list of raw information
def get_virtualservernames():
    vs_list = ns_getvs()
    vs_names = []
    for vs_unity in vs_list:
        vs_names.append(vs_unity['name'])
    return vs_names


#Get VSs VIP
def get_vsvip():
    vs_list = get_vs()
    vs_vip_index = {}
    for vs_unity in vs_list:
        vs_name = vs_unity['name']
        if 'ipv46' in vs_unity:
            vs_ip = vs_unity['ipv46']
        else:
            vs_ip = 'no IP'
        vs_vip_index[vs_name] = vs_ip
    return vs_vip_index
        

#create a list of VSs and the service group bindings each VS is using
def get_vsservicegroup():
    url = 'http://' + ns_server + '/nitro/v1/config/lbvserver_servicegroup_binding?bulkbindings=yes' 
    headers = ns_creds
    r = requests.get(url,headers=headers,verify=False)
    r = json.loads(r.text)
    vs_servicegroup_list = r['lbvserver_servicegroup_binding']
    for vs_servicegroup_unity in vs_servicegroup_list:
        vs_servicegroup_unity.pop('stateflag')
        if 'servicegroupname' in vs_servicegroup_unity and 'servicename' in vs_servicegroup_unity:
            vs_servicegroup_unity.pop('servicename')
    return vs_servicegroup_list

#create a list of VSs and the service bindings each VS is using
def get_vsservice():
    url = 'http://' + ns_server + '/nitro/v1/config/lbvserver_service_binding?bulkbindings=yes'
    headers = ns_creds
    r = requests.get(url,headers=headers,verify=False)
    r = json.loads(r.text)
    if 'lbvserver_service_binding' in r:
        vs_service_list = r['lbvserver_service_binding']
        return vs_service_list
    else:
        return 'no service'


#get a list of raw information on all service groups
def get_servicegroup():
    url = 'http://' + ns_server + '/nitro/v1/config/servicegroup_binding?bulkbindings=yes'
    headers = ns_creds
    r = requests.get(url,headers=headers,verify=False)
    r = json.loads(r.text)
    servicegroup_list = r['servicegroup_binding']
    return servicegroup_list


#get a list of raw information on all services
def get_service():
    url = 'http://' + ns_server + '/nitro/v1/config/service_binding?bulkbindings=yes'
    headers = ns_creds
    r = requests.get(url,headers=headers,verify=False)
    r = json.loads(r.text)
    service_list = r['service_binding']
    return service_list


#create a list of service groups with the IP address for each server that is member of the service group
def get_servicegroupips():
    servicegroup_list = get_servicegroup()
    servicegroupips = {}
    for servicegroup_unity in servicegroup_list:
        groupname = servicegroup_unity['servicegroupname']
        servicegroupips[groupname] = []
        if 'servicegroup_servicegroupmember_binding' in servicegroup_unity:
            for service_unity in servicegroup_unity['servicegroup_servicegroupmember_binding']:
                ip_address = service_unity['ip']
                servicegroupips[groupname].append(ip_address)
        else:
            print('Service group ' + groupname + ' has no members')
            print('')
    return servicegroupips

            
#get a list of VSs with the service group binding.
#get a list of service groups and the member IPs
#create a list of VS with the IPs of the member servers
def get_vsmembers():
    vsservicegroup_list = get_vsservicegroup() #####################################################
    servicegroupips_index = get_servicegroupips() #####################################################
    for vsservicegroup_unity in vsservicegroup_list:
        servicegroupname = vsservicegroup_unity['servicegroupname']
        vsservicegroup_unity['members'] = servicegroupips_index[servicegroupname]
    vsservice_list = get_vsservice()
    if vsservice_list != 'no service':
        for vsservice_unity in vsservice_list:
            vsname = vsservice_unity['name']
            servicename = vsservice_unity['servicename']
            members = vsservice_unity['ipv46']
            new_vs = {'name':vsname,'servicegroupname':servicename,'members':[members]}
            vsservicegroup_list.append(new_vs)
    return vsservicegroup_list


#converts a list of dictionaries into a csv    
def dicts_to_csv(list_of_dicts, filename):
    # Extract the keys from the first dictionary in the list
    keys = list_of_dicts[0].keys()
    #keys = ['name','loc','env','app','role']

    # Open the CSV file in write mode
    with open(filename, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=keys)

        # Write the header row
        writer.writeheader()

        # Write the rows for each dictionary
        for dictionary in list_of_dicts:
            writer.writerow(dictionary)        


#add VIP information to each VS
def compile_vsinfo():
    vs_list = get_vsmembers()
    vsvip_index = get_vsvip()
    for vs_unity in vs_list:
        vs_name = vs_unity['name']
        vs_unity['VIP'] = vsvip_index[vs_name]
    return vs_list

def help():
    print('get_vsmembers() - return a list of VS with the IPs of the member servers')
    print('dicts_to_csv(list_of_dicts, filename) - converts a list of dictionaries into a csv')

def vsmembers_to_csv():
    vs = compile_vsinfo()
    csv = input('enter csv file name: ')
    if '.csv' not in csv:
        csv = csv + '.csv'
    dicts_to_csv(vs,csv)
        
     
    
ns_login()
vsmembers_to_csv()

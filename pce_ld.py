# %%
import pce_auth,requests,getpass,json,time,pce_async_req,code
#code.interact(local=dict(globals(),**locals()))

def login_error_handling():
    try: auth_creds
    except NameError:
        print('***************************************************************')
        print('Enter PCE login information before proceeding')
        print('***************************************************************')
        login()


def login():
    global auth_creds, server,base_url_orgid,base_url
    try:
        auth_creds,base_url_orgid,base_url = pce_auth.connect()
    except TypeError:
        print('Connection Failed')


def get_rulesets():
    global auth_creds,base_url
    api_url = base_url_orgid + '/sec_policy/draft/rule_sets'
    r = pce_async_req.getdata(api_url,auth_creds,base_url)
    return(r)


def get_labels():
    global auth_creds,server
    api_url = base_url_orgid + '/labels'
    r = pce_async_req.getdata(api_url,auth_creds,base_url)
    return(r)


def get_iplists():
    global auth_creds,server
    api_url = base_url_orgid + '/sec_policy/draft/ip_lists'
    r = pce_async_req.getdata(api_url,auth_creds,base_url)
    return(r)

def get_virtual_servers():
    global auth_creds,server
    api_url = base_url_orgid + '/sec_policy/draft/virtual_servers'
    r = pce_async_req.getdata(api_url,auth_creds,base_url)
    return(r)

def get_vens():
    global auth_creds,server
    api_url = base_url_orgid + '/vens'
    r = pce_async_req.getdata(api_url,auth_creds,base_url)
    return(r)

def get_workloads():
    global auth_creds,server
    api_url = base_url_orgid + '/workloads/'
    r = pce_async_req.getdata(api_url,auth_creds,base_url)
    return(r)


def get_services():
    global auth_creds,server
    api_url = base_url_orgid + '/sec_policy/draft/services/'
    r = pce_async_req.getdata(api_url,auth_creds,base_url)
    return(r)


def get_discovered_virtual_servers():
    global auth_creds,server
    api_url = base_url_orgid + '/discovered_virtual_servers/'
    r = pce_async_req.getdata(api_url,auth_creds,base_url)
    return(r)    


def get_slbs():
    global auth_creds,server
    api_url = base_url_orgid + '/slbs/'
    r = pce_async_req.getdata(api_url,auth_creds,base_url)
    return(r)   


def discovered_virtual_servers_to_slbs():
    discovered_virtual_server_list = get_discovered_virtual_servers()
    discovered_virtual_servers_to_slbs_index = {}
    slb_index = slbs()
    for i in discovered_virtual_server_list:
        slb_name = slb_index[i['slb']['href']]
        discovered_virtual_servers_to_slbs_index[i['href']] = slb_name
    return(discovered_virtual_servers_to_slbs_index)


def slbs():
    slb_list = get_slbs()
    slb_index = {}
    for i in slb_list:
        slb_index[i['href']] = i['name']
        slb_index[i['name']] = i['href']
    return(slb_index)


def services():
    global service_index
    service_index = {}
    service_ports = {}
    service_list = get_services()
    for i in service_list:
        service_index[i['href']] = i['name']
        service_index[i['name']] = i['href']
        if 'service_ports' in i:
            service_ports[i['name']] = i['service_ports']
    return(service_index,service_ports)
        

def virtual_servers():
    login_error_handling()
    global virtual_server_index
    virtual_server_index = {}
    virtual_server_list = get_virtual_servers()
    for i in virtual_server_list:
        virtual_server_index[i['href']] = i['discovered_virtual_server']['name']
        virtual_server_index[i['name']] = i['href']
    return(virtual_server_index)


def virtual_servers_specific_slb(slb):
    login_error_handling()
    global virtual_server_specific_slb_index
    virtual_server_specific_slb_index = {}
    virtual_server_list = get_virtual_servers()
    discovered_virtual_servers_to_slbs_index = discovered_virtual_servers_to_slbs()
    for vs_unity in virtual_server_list:
        vs_unity_discovered_vs_href = vs_unity['discovered_virtual_server']['href']
        vs_unity_slb = discovered_virtual_servers_to_slbs_index[vs_unity_discovered_vs_href]
        if vs_unity_slb == slb:
            virtual_server_specific_slb_index[vs_unity['href']] = vs_unity['discovered_virtual_server']['name']
            virtual_server_specific_slb_index[vs_unity['name']] = vs_unity['href']
    return(virtual_server_specific_slb_index,discovered_virtual_servers_to_slbs_index)


def label_type():
    login_error_handling()
    global label_index
    labels_type_index = {}
    label_list = get_labels()
    for i in label_list:
        labels_type_index[i['href']] = i['key']
    return(labels_type_index)

def labels():
    login_error_handling()
    global label_index
    label_index = {}
    label_list = get_labels()
    for i in label_list:
        label_index[i['href']] = i['value']
        label_index[i['value']] = i['href']
    return(label_index)


def iplists():
    iplist_list = get_iplists()
    iplist_index = {}
    for i in iplist_list:
        iplist_index[i['href']] = i['name']
        iplist_index[i['name']] = i['href']
    return(iplist_index)


def labels_and_iplists():
    label_and_iplist_index = {}
    labels_var = labels()
    iplists_var = iplists()
    for k,v in labels_var.items():
        if k not in label_and_iplist_index:
            label_and_iplist_index[k] = v
    for k,v in iplists_var.items():
        if k not in label_and_iplist_index:
            label_and_iplist_index[k] = v
    return(label_and_iplist_index)


def workloads():
    login_error_handling()
    global workload_index,workload_list
    workload_index = {}
    workload_list = get_workloads()
    for i in workload_list:
        if i['name'] != None :
            if i['name'] in workload_index:
                print(i['name'],' - Duplicated')
            workload_index[i['href']] = i['name']
            workload_index[i['name']] = i['href']
        else:
            if i['hostname'] != '':
                if i['hostname'] in workload_index:
                    print(i['hostname'],' - Duplicated')
                workload_index[i['href']] = i['hostname']
                workload_index[i['hostname']] = i['href']
    return(workload_index,workload_list)


def rulesets():
    global ruleset_index,ruleset_list
    ruleset_list = get_rulesets()
    ruleset_index = {}
    for i in ruleset_list:
        ruleset_index[i['href']] = i['name']
        ruleset_index[i['name']] = i['href']
    return(ruleset_index,ruleset_list)


def print_ruleset_scope():
    global label_index,ruleset_list
    for i in ruleset_list:
                        print(i['name'])
                        for j in i['scopes'][0]:
                            print('    ',label_index[j['label']['href']])
                        print(' ')

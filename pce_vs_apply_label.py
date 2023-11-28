import pce_ld,pce_auth,json,csv,ast,code,sys,requests
#code.interact(local=dict(globals(),**locals()))

################################################################
#login block
def login_error_handling():
    try: base_url
    except NameError:
        print('***************************************************************')
        print('Enter PCE login information before proceeding')
        print('***************************************************************')
        try: ll()
        except FileNotFoundError:
            pce_auth.host = ''
        login()


def login():
    global auth_creds, server, base_url_orgid, base_url
    try:
        auth_creds,base_url_orgid,base_url = pce_auth.connect()
        pce_ld.auth_creds = auth_creds
        pce_ld.base_url_orgid = base_url_orgid
        pce_ld.base_url = base_url
    except TypeError:
        print('')



def save_login():
    pce_auth.save()


def ll():
    pce_auth.load_host()

################################################################
#load file block
#converts csv file into dictionary.
def csv_to_dict(filename):
    data = {}
    
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 2:
                key = row[0]
                value = row[1]
                if key != 'Key':
                    data[key] = ast.literal_eval(value)
    
    return data


def get_workload_file():
    filename = input('Enter the name of the file with the Workload labels: ')
    workload_new_label_index = csv_to_dict(filename)
    return workload_new_label_index


def get_vs_file():
    filename = input('Enter the name of the file with the Virtual Server member labels: ')
    vs_members_new_label_index = csv_to_dict(filename)
    return vs_members_new_label_index


################################################################
#Prepare Labels to be configured block


def define_new_app_labels(workload_new_label_index,pattern,label_index):
    app_labels_list = []
    new_app_labels_list = []
    for workload_unity,workload_labels in workload_new_label_index.items():
        for label_unity in workload_labels:
            if pattern in label_unity:
                app_labels_list.append(label_unity)
    for label in app_labels_list:
        if label not in label_index and label not in new_app_labels_list:
            new_app_labels_list.append(label)
    return new_app_labels_list


def create_new_labels(new_app_labels_list):
    for label in new_app_labels_list:
        url = base_url_orgid + '/labels'
        data = {'key':'app','value':label}
        data = json.dumps(data)
        r = requests.post(url,auth=auth_creds,data=data,verify=False)
        if r.status_code not in [200,201,202,203,204]:
            print(r.text)
        
#################################################################
#Apply Labels block
        

def convert_label_href(workload_or_vs_label_index,label_index):
    workload_new_label_index_href = {}
    for workload_or_vs_unity,labels in workload_or_vs_label_index.items():
        workload_new_label_index_href[workload_or_vs_unity] = []
        for label in labels:
            label_href = label_index[label]
            workload_new_label_index_href[workload_or_vs_unity].append(label_href)
    return workload_new_label_index_href


def format_put_data(new_label_index_href):
    new_label_index_put = {}
    for workload_unity,labels in new_label_index_href.items():
        new_label_index_put[workload_unity] = []
        for label in labels:
            new_label_index_put[workload_unity].append({'href':label})
    return new_label_index_put


def format_vs_put_data(new_label_index_href):
    new_label_index_put = {}
    for workload_unity,labels in new_label_index_href.items():
        new_label_index_put[workload_unity] = []
        for label in labels:
            new_label_index_put[workload_unity].append({'label':{'href':label}})
    return new_label_index_put


def apply_labels_to_workload(workload_new_label_index_put,workload_index):
    for workload_unity,labels in workload_new_label_index_put.items():
        workload_href = workload_index[workload_unity]
        url = base_url + workload_href
        data = {'labels':labels}
        data = json.dumps(data)
        r = requests.put(url,auth=auth_creds,data=data,verify=False)
        if r.status_code not in [200,201,202,203,204]:
            print(r.text)
        #print(r.text)
        
    
def apply_labels_to_vs_members(vs_members_new_label_index_put,vs_index,label_type_index,label_index):
    for vs_unity,labels in vs_members_new_label_index_put.items():
        vs_labels_list = []
        vs_members_data = {}
        vs_members = {'providers':labels}
        for label in labels:
            if label_type_index[label['label']['href']] == 'env' or label_type_index[label['label']['href']] == 'loc':
                vs_labels_list.append(label['label'])
        vs_labels_list.append({'href':label_index['A-' + vs_unity]})
        vs_labels_list.append({'href':label_index['R-VIP']})
        #code.interact(local=dict(globals(),**locals()))
        vs_labels_data = {'labels':vs_labels_list}
        data = {**vs_members, **vs_labels_data}
        data = json.dumps(data)
        #code.interact(local=dict(globals(),**locals()))
        if vs_unity in vs_index:
            vs_href = vs_index[vs_unity]
            url = base_url + vs_href
            r = requests.put(url,auth=auth_creds,data=data,verify=False)
            if r.status_code not in [200,201,202,203,204]:
                print(r.text)
        #code.interact(local=dict(globals(),**locals()))
        

def create_vs_app_label_names(vs_members_new_label_index_put,label_index):
    for vs_unity in vs_members_new_label_index_put:
        vs_app_label_name = 'A-' + vs_unity
        if vs_app_label_name not in label_index:
            create_new_labels([vs_app_label_name])    
        


####################################################################
#Configure VS as managed block
        
def get_discovered_virtual_servers():
    r = pce_ld.get_discovered_virtual_servers()
    discovered_server_list = r
    return discovered_server_list

    
def get_missing_vs(vs_index,vs_members_new_label_index):
    new_vs_list = []
    for vs in vs_members_new_label_index:
        if vs not in vs_index:
            new_vs_list.append(vs)
    return new_vs_list


def create_vs(new_vs_list,discovered_virtual_servers_to_slbs_index,slb):
    discovered_virtual_server_list = get_discovered_virtual_servers()
    for new_vs_unity in new_vs_list:
        for discovered_server_unity in discovered_virtual_server_list:
            discovered_server_unity_href = discovered_server_unity['href']
            #code.interact(local=dict(globals(),**locals()))
            discovered_server_unity_slb = discovered_virtual_servers_to_slbs_index[discovered_server_unity_href]
            if discovered_server_unity['name'] == new_vs_unity and discovered_server_unity_slb == slb:
                if discovered_server_unity['virtual_server'] == None:
                    data = {"name":new_vs_unity,"discovered_virtual_server":{"href":discovered_server_unity['href']},"labels":[],"service":{"href":"/orgs/1/sec_policy/draft/services/1"},"providers":[],"mode":"unmanaged"}
                    data = json.dumps(data)
                    url = base_url_orgid + '/sec_policy/draft/virtual_servers'
                    r = requests.post(url,data=data,auth=auth_creds,verify=False)
                    if r.status_code not in [200,201,202,203,204]:
                        print(r.text)
    
    

################################################################
#Execution block


def main():
    login()
    workload_index,workload_list = pce_ld.workloads()
    label_index = pce_ld.labels()
    slb = input('Enter the name of the specific NetScaler: ')
    vs_index,discovered_virtual_servers_to_slbs_index = pce_ld.virtual_servers_specific_slb(slb)
    workload_new_label_index = get_workload_file()
    vs_members_new_label_index = get_vs_file()
    new_app_labels_list = define_new_app_labels(workload_new_label_index,'A-NSG-',label_index)
    create_new_labels(new_app_labels_list)
    label_index = pce_ld.labels()
    workload_new_label_index_href = convert_label_href(workload_new_label_index,label_index)
    vs_members_new_label_index_href = convert_label_href(vs_members_new_label_index,label_index)
    workload_new_label_index_put = format_put_data(workload_new_label_index_href)
    apply_labels_to_workload(workload_new_label_index_put,workload_index)
    vs_members_new_label_index_put = format_vs_put_data(vs_members_new_label_index_href)
    new_vs_list = get_missing_vs(vs_index,vs_members_new_label_index)
    create_vs(new_vs_list,discovered_virtual_servers_to_slbs_index,slb)### check that the VS is only created if the discovered VS uses the selected SLB
    create_vs_app_label_names(vs_members_new_label_index_put,label_index)
    label_type_index = pce_ld.label_type()
    vs_index,discovered_virtual_servers_to_slbs_index = pce_ld.virtual_servers_specific_slb(slb)### Use the new pce_ld.virtual_servers_specific_slb
    label_index = pce_ld.labels()
    apply_labels_to_vs_members(vs_members_new_label_index_put,vs_index,label_type_index,label_index)


#main()

    

    
    

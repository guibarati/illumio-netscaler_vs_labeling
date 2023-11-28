import pce_ld,pce_auth,json,csv,ast,code,sys
#code.interact(local=dict(globals(),**locals()))


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


#converts csv file into dictionary.
def csv_to_dicts(filename):
    dicts = []
    # Open the CSV file in read mode
    try:
        with open(filename, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            # Iterate over each row in the CSV file
            for row in reader:
                for column in row:
                    if '[' in row[column]:
                        row[column] = ast.literal_eval(row[column])
                dicts.append(row)
    except FileNotFoundError:
        print('File not found.')
        print('')
        exit()
    return dicts


#Loads the CSV information into variable
def load_data():
    global ns_virtualserver_lisr
    filename = input('Enter the filename for the CSV file with the NetScaler export: ')
    csv = csv_to_dicts(filename)
    columns = ['name','members']
    for i in columns:
        if i not in csv[0].keys():
            print('CSV file must have the columns "name" and "members"')
            return
    ns_virtualserver_list = csv
    return ns_virtualserver_list

def dict_to_csv(data, filename):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Key', 'Value'])
        for key, value in data.items():
            writer.writerow([key, value])
            

################################################################
def export_workloads_and_vs_members(workload_full_labels,vs_member_labels):
    name = input('Enter the name to identify the export files: ')
    if '.csv' not in name:
        name = name + '.csv'
    workload_file_name = 'workload-' + name
    dict_to_csv(workload_full_labels, workload_file_name)
    vs_file_name = 'vs_members-' + name
    dict_to_csv(vs_member_labels, vs_file_name)

#################################################################
#creates an index with servers and grouping numbers.
def define_groups(vs_list):
    servergrouping_index = {}
    servergrouping_dedup_list =[]
    for vs_unity in vs_list:
        if vs_unity['members'] not in servergrouping_dedup_list:
            servergrouping_dedup_list.append(vs_unity['members'])
    for servergrouping_unity in servergrouping_dedup_list:
        for member in servergrouping_unity:
            if member in servergrouping_index:
                #code.interact(local=dict(globals(),**locals()))
                for member2 in servergrouping_unity:
                    servergrouping_index[member2] = servergrouping_index[member]
            if member not in servergrouping_index:
                servergrouping_index[member] = servergrouping_dedup_list.index(servergrouping_unity)+1
    return servergrouping_index
            

    
def ip_to_workload(servergrouping_index):
    login_error_handling()
    workload_list = pce_ld.get_workloads()
    ip_to_workload_index = {}
    found_workloads_list = []
    for member_ip in servergrouping_index.keys():
        for workload_unity in workload_list:
            if workload_unity['hostname'] != '':
                workload_name = workload_unity['hostname']
            else:
                workload_name = workload_unity['name']
            for interface_unity in workload_unity['interfaces']:
                if interface_unity['address'] == member_ip:
                    ip_to_workload_index[member_ip] = workload_name
                    found_workloads_list.append(interface_unity['address'])
    for member_ip in servergrouping_index.keys():
        if member_ip not in found_workloads_list:
            print('IP Address - ' + member_ip + ' - has no matching workload')
    return ip_to_workload_index


def get_vs_member_grouping(vs_list,servergrouping_index):
    vs_member_grouping = {}
    for vs_unity in vs_list:
        name = vs_unity['name']
        if len(vs_unity['members']) > 0:
            member1 = vs_unity['members'][0]
            grouping = servergrouping_index[member1]
            vs_member_grouping[name] = grouping
    return vs_member_grouping


def check_workload_with_multi_ips(servergrouping_index,ip_to_workload_index):
    workload_to_ip_index = {}
    for ip, name in ip_to_workload_index.items():
        if name not in workload_to_ip_index:
            workload_to_ip_index[name] = ip
        elif name in workload_to_ip_index:
            server_old_grouping = servergrouping_index[ip]
            server_new_grouping = servergrouping_index[workload_to_ip_index[name]]
            servergrouping_index[ip] = servergrouping_index[workload_to_ip_index[name]]
            for ip_2,grouping in servergrouping_index.items():
                if grouping == server_old_grouping:
                    servergrouping_index[ip_2] = servergrouping_index[workload_to_ip_index[name]]
    return servergrouping_index
    


###############################################################################################################
def get_workload_grouping_index(servergrouping_index):
    #servergrouping_index = define_groups(vs_list)
    ip_to_workload_index = ip_to_workload(servergrouping_index)
    
    servergrouping_index = check_workload_with_multi_ips(servergrouping_index,ip_to_workload_index)
    
    workload_grouping_index = {}
    for key,value in ip_to_workload_index.items():
        name = value
        grouping = servergrouping_index[key]
        workload_grouping_index[name] = grouping
    return workload_grouping_index,servergrouping_index
        



def get_vs_member_labels(vs_member_grouping,workload_grouping_index,workload_full_labels):
    vs_member_labels = {}
    for vs_unity,vs_grouping in vs_member_grouping.items():
        for workload_grouping_unity,workload_grouping in workload_grouping_index.items():
            if vs_grouping == workload_grouping:
                vs_member_labels[vs_unity] = workload_full_labels[workload_grouping_unity]
                break
    return vs_member_labels





def get_virtualserver():
    login_error_handling()
    #get full collection of virtual servers with all attributes
    vs_raw = pce_ld.get_virtual_servers()
    #create an index of label names to href and names to type
    label_type = pce_ld.label_type()
    label_index = pce_ld.labels()
    #Create a list of dictionaries with only the relevant VS information
    pce_vs_list = []
    for i in vs_raw:
        vs_dict = {}
        vs_dict['name'] = i['name']
        for j in i['labels']:
            label_href = j['href']
            l_type = label_type[label_href]
            vs_dict[l_type] = label_index[label_href]
        pce_vs_list.append(vs_dict)
    return pce_vs_list

########################################################

def get_workload_labels():
    workload_list = pce_ld.get_workloads()
    workload_label_index = {}
    for workload_unity in workload_list:
        if workload_unity['hostname'] != '':
            workload_name = workload_unity['hostname']
        else:
            workload_name = workload_unity['name']
        #name = workload_unity['hostname']
        labels = workload_unity['labels']
        workload_label_index[workload_name]=labels
    return(workload_label_index)


def find_app_label(workload_labels):
    app_label = ''
    for i in workload_labels:
        if 'key' in i:
            if i['key']=='app':
                app_label = i['value']
    return app_label


def define_label(pattern,workload_grouping_index):
    workload_label_index = get_workload_labels()
    workload_new_app_labels = {}
    last_label_number = find_last_label(pattern)
        
    for workload_unity in workload_grouping_index:
        if workload_unity not in workload_new_app_labels:
            app_label = find_app_label(workload_label_index[workload_unity])
        else:
            app_label = workload_new_app_labels[workload_unity]
        if pattern in app_label:
            workload_new_app_labels[workload_unity] = app_label
            for workload_unity2 in workload_grouping_index:
                #code.interact(local=dict(globals(),**locals()))
                workload1_group = workload_grouping_index[workload_unity]
                workload2_group = workload_grouping_index[workload_unity2]
                if workload1_group == workload2_group:
                    workload_new_app_labels[workload_unity2] = app_label
        else:
            #code.interact(local=dict(globals(),**locals()))
            workload_unity_grouping = int(workload_grouping_index[workload_unity])
            label_sequence = str(int(last_label_number) + int(workload_unity_grouping))
            label_sequence = label_sequence.zfill(4)
            app_label_compile = pattern + label_sequence
            workload_new_app_labels[workload_unity] = app_label_compile
    return workload_label_index,workload_new_app_labels
            

def update_app_label(workload_label_index,workload_new_app_labels):
    workload_full_labels = {}
    for workload_unity in workload_new_app_labels:
        workload_full_labels[workload_unity] = []
        if workload_unity in workload_label_index:
            for label in workload_label_index[workload_unity]:
                if 'key' in label:
                    if label['key'] != 'app':
                        workload_full_labels[workload_unity].append(label['value'])
            workload_full_labels[workload_unity].append(workload_new_app_labels[workload_unity])
    return workload_full_labels
            
    
#########################################################
#Find last label
def get_pce_label_list():
    login_error_handling()
    pce_labels_raw = pce_ld.get_labels()
    pce_label_list = []
    for label_unity in pce_labels_raw:
        name = label_unity['value']
        pce_label_list.append(name)
    return pce_label_list


def find_last_label(pattern):
    pce_label_list_withpattern = []
    pce_label_list = get_pce_label_list()
    last_label=''
    for label_unity in pce_label_list:
        #code.interact(local=dict(globals(),**locals()))
        if pattern in label_unity:
            pce_label_list_withpattern.append(label_unity)
    pce_label_list_withpattern.sort()
    if len(pce_label_list_withpattern) > 0:
        last_label = pce_label_list_withpattern[-1]

    label_sequence = ''
    for i in reversed(last_label):
        if i.isdigit():
            label_sequence = i + label_sequence
    if label_sequence.isdigit():
        last_label_number = int(label_sequence)
    else:
        last_label_number = 0
    return last_label_number
##########################################################



    
def verify_duplicates(vs_list):
    has_duplicates = 0
    servergrouping_index = {}
    servergrouping_dedup_list =[]
    for vs_unity in vs_list:
        if vs_unity['members'] not in servergrouping_dedup_list:
            servergrouping_dedup_list.append(vs_unity['members'])
            
    for servergrouping_unity in servergrouping_dedup_list:
        for member in servergrouping_unity:
            if member in servergrouping_index:
                print('----------------------------------------------------------------------')
                print('server : ' + member + ' is part of more than one Service Group. All servers will be grouped together')
                for servergrouping_unity in servergrouping_dedup_list:
                    if member in servergrouping_unity:
                        print(servergrouping_unity)
                print('----------------------------------------------------------------------')
            if member not in servergrouping_index:
                servergrouping_index[member] = servergrouping_dedup_list.index(servergrouping_unity)
##########################################################                
def main():
    global vs_list,servergrouping_index,workload_grouping_index,vs_member_grouping
    global workload_label_index,workload_new_app_labels,workload_full_labels
    global vs_member_labels
    vs_list = load_data()
    servergrouping_index = define_groups(vs_list)
    workload_grouping_index,servergrouping_index = get_workload_grouping_index(servergrouping_index)
    vs_member_grouping = get_vs_member_grouping(vs_list,servergrouping_index)
    workload_label_index,workload_new_app_labels = define_label('A-NSG-',workload_grouping_index)
    workload_full_labels = update_app_label(workload_label_index,workload_new_app_labels)
    vs_member_labels = get_vs_member_labels(vs_member_grouping,workload_grouping_index,workload_full_labels)
    export_workloads_and_vs_members(workload_full_labels,vs_member_labels)
    
    
    
def help():
    print('Use the options below:')
    print('    duplicates -> find IPs that belong to different groupings')
    print('    workloads  -> find IPs that have no matching workload on the PCE')
    print('    labels     -> creates two csv files. One for the workload labeling, one for the Virtual server member labeling')


def initiate():
    args = sys.argv
    if len(args) > 1:
        if args[1] == 'duplicates':
            file = load_data()
            servergrouping_index = verify_duplicates(file)
        elif args[1] == 'workloads':
            file = load_data()
            servergrouping_index = define_groups(file)
            ip_to_workload_index = ip_to_workload(servergrouping_index)
        elif args[1] == 'labels':
            login()
            main()
    else:
        help()
            


initiate()
    

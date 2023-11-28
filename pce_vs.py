import requests,pce_ld,pce_auth,os,code,json,csv,sys
#code.interact(local=dict(globals(),**locals()))



def initiate():
    args = sys.argv
    if len(args) > 2:
        if args[1] == 'import':
            import_vs(args[2])
        elif args[1] == 'export':
            export_vs(args[2])
        else:
            print('"'+args[1]+'"' + ' command is not supported')
            print('Valid commands are "import", "export"')
    else:
        print('Valid commands are "import", "export"')        


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
    auth_creds,base_url_orgid,base_url = pce_auth.connect()
    pce_ld.auth_creds = auth_creds
    pce_ld.base_url_orgid = base_url_orgid
    pce_ld.base_url = base_url

def save_login():
    pce_auth.save()


def ll():
    pce_auth.load_host()


def dicts_to_csv(list_of_dicts, filename):
    # Extract the keys from the first dictionary in the list
    #keys = list_of_dicts[0].keys()
    keys = ['name','loc','env','app','role']

    # Open the CSV file in write mode
    with open(filename, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=keys)

        # Write the header row
        writer.writeheader()

        # Write the rows for each dictionary
        for dictionary in list_of_dicts:
            writer.writerow(dictionary)

def csv_to_dicts(filename):
    dicts = []

    # Open the CSV file in read mode
    with open(filename, 'r') as csv_file:
        reader = csv.DictReader(csv_file)

        # Iterate over each row in the CSV file
        for row in reader:
            dicts.append(row)

    return dicts


def virtual_servers():
    #get full collection of virtual servers with all attributes
    vs_raw = pce_ld.get_virtual_servers()
    #create an index of label names to href and names to type
    label_type = pce_ld.label_type()
    label_index = pce_ld.labels()
    #Create a list of dictionaries with only the relevant VS information
    vs_list = []
    for i in vs_raw:
        vs_dict = {}
        vs_dict['name'] = i['name']
        for j in i['labels']:
            label_href = j['href']
            l_type = label_type[label_href]
            vs_dict[l_type] = label_index[label_href]
        vs_list.append(vs_dict)
    return(vs_list)
        

def export_vs(file=None):
    #check if it's logged in to PCE
    login_error_handling()
    #saves the login information
    save_login()
    #loads list of dictionaries with relevant VS information for editing
    vs = virtual_servers()
    if file == None:
        file = input('Virtual Servers CSV file: ')
    #saves dictionary to csv file
    dicts_to_csv(vs,file)
    

def import_vs(file=None):
    login_error_handling()
    save_login()
    has_new_label = 0
    if file == None:
        file = input('Virtual Servers CSV file: ')
    vs = csv_to_dicts(file)
    label_index = pce_ld.labels()
    virtual_servers = pce_ld.virtual_servers()
    keys = ['loc','env','app','role']
    #go through all VSs on the list
    for i in vs:
        #check if each dictionary has each label type
        for j in keys:
            #if it has the label type in the csv, check if the label is created
            if j in i:
                #if the label is not created, create it.
                if i[j] not in label_index and i[j] != '':
                    create_label(j,i[j])
                    has_new_label = 1
    if has_new_label == 1:
        label_index = pce_ld.labels()

    for i in vs:
        label_names = []
        for key,value in i.items():
            if key != 'name' and key != 'providers':
                label_names.append(value)
        i['label_names'] = label_names
        
    for i in vs:
        label_hrefs = []
        for j in i['label_names']:
            if j != '':
                label_hrefs.append({'href':label_index[j]})
        i['label_hrefs'] = label_hrefs
        vs_name = i['name']
        i ['href'] = virtual_servers[vs_name]
        
    for i in vs:
        vs_name = i['name']
        vs_href = i['href']
        url = base_url + vs_href
        vs_individual = {}
        vs_individual['labels'] = i['label_hrefs']
        data = json.dumps(vs_individual)
        r = requests.put(url,auth=auth_creds,data=data,verify=False)
        print(vs_name + ' - ' + str(r.status_code))


def create_label(key,name):
    label = {'key':key,'value':name}
    data = json.dumps(label)
    url = base_url_orgid + '/labels'
    r = requests.post(url,auth=auth_creds,data=data,verify=False)


initiate()

    

import requests,json,csv,code


def ns_login():
    global ns_user,ns_server,ns_creds
    ns_server = input('Server fqdn:port : ')
    ns_user = input('Username : ')
    ns_pass = input('Password : ')
    ns_creds = {'X-NITRO-User': ns_user, 'X-NITRO-PASS':ns_pass}
    #return ns_server,ns_creds


def get_vs():
    ns_login()
    url =  'http://' + ns_server + '/nitro/v1/config/lbvserver/'
    headers = ns_creds
    r = requests.get(url,headers=headers,verify=False)
    r = json.loads(r.text)
    virtualserver_list = r['lbvserver']
    return virtualserver_list


def get_service_types():
    vs_list = get_vs()
    service_types = []
    for vs_unity in vs_list:
        if 'servicetype' in vs_unity:
            #if vs_unity['servicetype'] not in service_types:
            service_types.append(vs_unity['servicetype'])
    return service_types


def write_list_to_csv(my_list, filename):
    with open(filename, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        for item in my_list:
            writer.writerow([item])

write_list_to_csv(get_service_types(), 'service_types.csv')

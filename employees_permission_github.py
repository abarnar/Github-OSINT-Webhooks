import os
import requests
import csv

def get_headers():
    github_token = os.environ.get('GITHUB_TOKEN')
    headers = {'Authorization': 'token ' + github_token}
    return headers

def check_env():
    if os.environ.get('GITHUB_TOKEN') is None:
        print("Please enter the Github token as an Environment variable!")
        print_required_env()
        exit()

    if os.environ.get('EMPLOYEES_EMAIL_CSV_FILE_PATH') is None:
        print("Please enter the employee email csv file path as an Environment variable!")
        print_required_env()
        exit()

    if os.environ.get('GITHUB_ORG_NAMES') is None:
        print("Please enter Github org names (comma-separated) as an Environment variable!")
        print_required_env()
        exit()

def print_required_env():
    print('The FOLLOWING variable that has to be set\n1.GITHUB_TOKEN\n2.EMPLOYEES_EMAIL_CSV_FILE_PATH\n3.GITHUB_ORG_NAMES')

def get_org_repo_name_list(repo_information_response):
    repository_name_list = []
    for i in repo_information_response:
        repository_name_list.append(i['name'])
    return repository_name_list

def read_input_from_csv(csv_file_path):
    with open(csv_file_path, 'r') as file:
        reader = csv.reader(file)
        user_email_list = []
        for row in reader:
            user_email_list.append(row[0])
    return user_email_list

def repo_information_list(org_name):
    org_repo_url='https://api.github.com/orgs/' + org_name + '/repos'
    repo_name_response = requests.get((org_repo_url), headers=get_headers())
    if repo_name_response.status_code == 200 :
        final_repo_list = get_org_repo_name_list(repo_name_response.json())
        while 'next' in repo_name_response.links:
            repo_name_response = requests.get(repo_name_response.links['next']['url'], headers=get_headers())
            final_repo_list.extend(get_org_repo_name_list(repo_name_response.json()))
    return final_repo_list

def get_org_member_name_list(member_information_response):
    members_name_list = []
    for i in member_information_response:
        members_name_list.append(i['login'])
    return members_name_list

def member_information_list(repository):
    org_members_url = 'https://api.github.com/orgs/' + repository + '/members'
    members_response = requests.get((org_members_url), headers=get_headers())
    if members_response.status_code == 200 :
        final_members_list = get_org_member_name_list(members_response.json())
        while 'next' in members_response.links:
            members_response = requests.get(members_response.links['next']['url'], headers=get_headers())
            final_members_list.extend(get_org_member_name_list(members_response.json()))
    return final_members_list

def get_username_vs_email_address(org_members_name_list,user_email_list):
    username_email_map = {}
    for i in org_members_name_list:
        user_response = requests.get('https://api.github.com/users/' + i,  headers=get_headers())
        if user_response.status_code == 200:
            user_response_json = user_response.json()
            individual_user_email = user_response_json['email']
            if individual_user_email is not None and individual_user_email in user_email_list:
                username_email_map[i] = individual_user_email
    return username_email_map


def export_details_to_csv(username_vs_email_for_csv_input, org_name_vs_repo_list):
    with open('github_permission_info.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        column_name = ['Employee_Email', 'Employee_Github_Username', 'Github_Org',
                     'Github_Org_Repo_name', 'Employee_repository_permission_available', 'is_admin']
        writer.writerow(column_name)
        for username in username_vs_email_for_csv_input:
            user_email = username_vs_email_for_csv_input[username]
            for org in org_name_vs_repo_list:
                repo_list = org_name_vs_repo_list[org]
                for repo_name in repo_list:
                    repo_permission_url = 'https://api.github.com/repos/' + org + '/' + repo_name + '/collaborators/' + username + '/permission'
                    permission_response = requests.get((repo_permission_url), headers=get_headers())
                    if permission_response.status_code == 200:
                        print("200")
                        permission_response_json = permission_response.json()
                        permission_meta = permission_response_json['permission']
                        is_admin = permission_response_json['user']['site_admin']
                        csv_row = []
                        csv_row.append(user_email)
                        csv_row.append(username)
                        csv_row.append(org)
                        csv_row.append(repo_name)
                        csv_row.append(permission_meta)
                        csv_row.append(is_admin)
                        writer.writerow(csv_row)


if (__name__ == "__main__"):
    check_env()
    csv_file_path = os.environ.get('EMPLOYEES_EMAIL_CSV_FILE_PATH')
    user_email_list = read_input_from_csv(csv_file_path)
    org_name_list = os.environ.get('GITHUB_ORG_NAMES').split(',')
    org_repo_name_list = []
    org_name_vs_repo_list = {}
    for i in org_name_list:
        repo_names = repo_information_list(i)
        org_name_vs_repo_list[i] = repo_names
        org_repo_name_list.extend(repo_names)
    print("Total number of repositories", len(org_repo_name_list))
    org_members_name_list = []
    for i in org_name_list:
        membernames = member_information_list(i)
        org_members_name_list.extend(membernames)
    org_members_name_list = list(set(org_members_name_list))
    print("Total number of unique members in Github organisations", len(org_members_name_list))
    username_vs_email_for_csv_input = get_username_vs_email_address(org_members_name_list,user_email_list)
    print(username_vs_email_for_csv_input)
    export_details_to_csv(username_vs_email_for_csv_input, org_name_vs_repo_list)


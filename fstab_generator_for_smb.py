import argparse
import csv
import os
import subprocess
import sys
import pdb

def build_remote_path(ip_address, remote_folder_name) -> str:

    # see: https://serverfault.com/questions/1000200/unable-to-mount-cifs-share-in-fstab-with-spaces-in-share-name
    space_replacement_char = "\\040"
    
    return f"//{ip_address}/{remote_folder_name.replace(' ', space_replacement_char)}"

def construct_local_path(local_path):

    os.makedirs(local_path)


def parse_user_id(raw_user_id) -> int:
    """
    If the user ID in the CSV file is a number, use it directly.
    If it's anything else, e.g. a username directly "myusser" or even the user variable "$(USER)",
      get the user ID associated with that object
    """

    if str.isnumeric(raw_user_id):
        return raw_user_id
    
    else:
        user_id = subprocess.run(f"id -u {raw_user_id}", shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
        return int(user_id)
    

def parse_group_id(raw_group_id) -> int:
    """
    Same thing as `parse_user_id()` but for groups
    """

    if str.isnumeric(raw_group_id):
        return raw_group_id
    
    else:
        # the output of `getent` looks like: `<GROUP_NAME>:x:<GROUP_ID>:<USER>`
        group_id = subprocess.run(f"getent group {raw_group_id}", shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8').split(":")[2]
        return int(group_id)


def verify_chmod_permissions(permission_num_raw : str) -> bool:

    MAX_PERMISSION_NUM = 0o0777
    OCTAL_BASE = 8

    permission_num = int(permission_num_raw, OCTAL_BASE)

    return (permission_num > 0) and (permission_num <= MAX_PERMISSION_NUM)


def generate_fstab_line(remote_path, local_path, share_type, creds_file, user_id, group_id, file_mode, dir_mode, options) -> str:

    return f"{remote_path} {local_path} {share_type} credentials={creds_file},uid={user_id},gid={group_id},file_mode={file_mode},dir_mode={dir_mode}{options}"


if __name__ == "__main__":

    argparse_parser = argparse.ArgumentParser()
    
    argparse_parser.add_argument("-f", "--input-csv-file", type=str, required=True, help="The CSV filepath to read from")

    # TODO: Support lookup from MAC address
    argparse_parser.add_argument("-i", "--remote-ip-address", type=str, required=True, help="The IP address of the remote share. Only tested with IPv4")
    argparse_parser.add_argument("-r", "--remaining-text", type=str, required=False, help="Any remaining text to add in the line")

    argparse_args = argparse_parser.parse_args()

    with open(argparse_args.input_csv_file, "r") as csv_file:

        #csv_reader = csv.reader(csv_file, delimiter=",")

        #next(csv_reader) # skip headers

        #for line_num, line_contents in enumerate(csv_reader):

        csv_reader = csv.DictReader(csv_file)

        for csv_file_row in csv_reader:

            remote_path = build_remote_path(argparse_args.remote_ip_address, csv_file_row["remote folder name"])

            local_path = csv_file_row["local folder path"]
            construct_local_path(local_path)

            file_share_type = csv_file_row["file share type"]

            credential_file_path = csv_file_row["credential file path"]

            if not os.path.isfile(credential_file_path):
                sys.exit("Error: credentials file doesn't exist")

            #pdb.set_trace()

            user_id = parse_user_id(csv_file_row["user id"])
            group_id = parse_group_id(csv_file_row["group id"])

            file_permissions = csv_file_row["file mode"]
            if not verify_chmod_permissions(file_permissions):
                sys.exit("Invalid file permissions!")
            
            directory_permissions = csv_file_row["directory mode"]
            if not verify_chmod_permissions(directory_permissions):
                sys.exit("Invalid directory permissions")


            fstab_file = generate_fstab_line(remote_path, local_path, file_share_type, credential_file_path, user_id, group_id, file_permissions, directory_permissions, argparse_args.remaining_text)

            print(fstab_file)


            



        







        

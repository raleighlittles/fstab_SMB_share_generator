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

    os.makedirs(local_path, exist_ok=True)


def parse_user_id(raw_user_id) -> int:
    """
    If the user ID in the CSV file is a number, use it directly.
    If it's anything else, e.g. a username directly "myuser" or even the user variable "$(USER)",
      get the user ID associated with that object
    """

    if str.isnumeric(raw_user_id):
        return raw_user_id

    else:
        user_id = subprocess.run(f"id -u {raw_user_id}",
                                 shell=True,
                                 stdout=subprocess.PIPE).stdout.decode('utf-8')
        return int(user_id)


def parse_group_id(raw_group_id) -> int:
    """
    Same thing as `parse_user_id()` but for groups
    """

    if str.isnumeric(raw_group_id):
        return raw_group_id

    else:
        # the output of `getent` looks like: `<GROUP_NAME>:x:<GROUP_ID>:<USER>`
        group_id = subprocess.run(
            f"getent group {raw_group_id}", shell=True,
            stdout=subprocess.PIPE).stdout.decode('utf-8').split(":")[2]
        return int(group_id)


def extract_symbolic_permissions(permission_str):
    """
    Convert symbolic permission notation to numeric notation.
    """

    allowed_symbolic_perms_chars = ["r", "w", "x", "-"]

    for ch in permission_str:
        if ch not in allowed_symbolic_perms_chars:
            raise ValueError(
                f"'{permission_str}' is not a valid symbolic permission string")

    perms = {
        '---': '0',
        '--x': '1',
        '-w-': '2',
        '-wx': '3',
        'r--': '4',
        'r-x': '5',
        'rw-': '6',
        'rwx': '7'
    }

    # Trim Lead If It Exists
    if len(permission_str) == 10:
        permission_str = permission_str[1:]

    # Parse Symbolic to Numeric
    x = (permission_str[:-6], permission_str[3:-3], permission_str[6:])
    numeric = perms[x[0]] + perms[x[1]] + perms[x[2]]
    return numeric


def verify_chmod_permissions(permission_num_raw: str) -> bool:

    MAX_PERMISSION_NUM = 0o0777
    OCTAL_BASE = 8

    permission_num = int(permission_num_raw, OCTAL_BASE)

    return (permission_num > 0) and (permission_num <= MAX_PERMISSION_NUM)


def parse_permissions(permission_str_raw):

    if permission_str_raw.isnumeric():
        # No conversion needed
        if not verify_chmod_permissions(permission_str_raw):
            raise ValueError(f"User provided permission string '{
                             permission_str_raw}' is invalid!")

        return permission_str_raw

    else:
        # User provided symbolic permissions, convert to numeric
        octal_perms = extract_symbolic_permissions(permission_str_raw.strip())

        return octal_perms


def generate_fstab_line(remote_path, local_path, share_type, creds_file,
                        user_id, group_id, file_mode, dir_mode,
                        options) -> str:

    return f"{remote_path} {local_path} {share_type} credentials={creds_file},uid={user_id},gid={group_id},file_mode={file_mode},dir_mode={dir_mode}{options}"


if __name__ == "__main__":

    argparse_parser = argparse.ArgumentParser()

    argparse_parser.add_argument("-f",
                                 "--input-csv-file",
                                 type=str,
                                 required=True,
                                 help="The CSV filepath to read from")
    argparse_parser.add_argument(
        "-i",
        "--remote-ip-address",
        type=str,
        required=True,
        help="The IP address of the remote share. Only tested with IPv4")
    argparse_parser.add_argument("-r",
                                 "--remaining-text",
                                 type=str,
                                 required=False,
                                 help="Any remaining text to add in the line")

    argparse_args = argparse_parser.parse_args()

    with open(argparse_args.input_csv_file, "r") as csv_file:

        csv_reader = csv.DictReader(csv_file)

        for csv_file_row in csv_reader:

            remote_path = build_remote_path(argparse_args.remote_ip_address,
                                            csv_file_row["remote directory name"])

            local_path = csv_file_row["local directory path"]
            construct_local_path(local_path)

            file_share_type = csv_file_row["file share type"]

            credential_file_path = csv_file_row["credential file path"]

            if not os.path.isfile(credential_file_path):
                print(
                    f"[ERROR] Credentials file {
                        credential_file_path} doesn't exist"
                )
                sys.exit(1)

            user_id = parse_user_id(csv_file_row["user id"])
            group_id = parse_group_id(csv_file_row["group id"])

            file_permissions = parse_permissions(csv_file_row["file mode"])

            directory_permissions = parse_permissions(
                csv_file_row["directory mode"])

            fstab_file = generate_fstab_line(remote_path, local_path,
                                             file_share_type,
                                             credential_file_path, user_id,
                                             group_id, file_permissions,
                                             directory_permissions,
                                             argparse_args.remaining_text)

            print(fstab_file)

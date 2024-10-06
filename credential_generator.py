import argparse
import os


def generate_credential_file(username, password, domain):

    credential_file_path = os.path.join( os.getenv("HOME"), ".smbcredentials")

    if os.path.exists(credential_file_path):
        raise FileExistsError(f"[ERROR] The file {credential_file_path} already exists")

    with open(credential_file_path, mode="w", encoding="utf-") as credential_file:
        credential_file.write(f"username={username}\n")
        credential_file.write(f"password={password}\n")

        if domain:
            credential_file.write(f"domain={domain}\n")
    

if __name__ == "__main__":
    argparse_parser = argparse.ArgumentParser()

    argparse_parser.add_argument("-u",
                                 "--username",
                                 type=str,
                                 required=True,
                                 help="The username to use")
    argparse_parser.add_argument("-p",
                                 "--password",
                                 type=str,
                                 required=True,
                                 help="The password to use")
    argparse_parser.add_argument("-d",
                                 "--domain",
                                 type=str,
                                 required=False,
                                 help="The domain to use")

    argparse_args = argparse_parser.parse_args()

    generate_credential_file(argparse_args.username, argparse_args.password,
                             argparse_args.domain)

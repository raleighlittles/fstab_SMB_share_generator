# About

This is a very simple Python script for generating `/etc/fstab` remote mounts, specifically catered towards Samba (SMB) shares.

I have a NAS with over 20 attached folders, so setting up shares manually would've taken too long and been too error-prone.

By filling out a simple CSV file and creating a credentials file, you can have a formatted `/etc/fstab` generated for you.


# Setup/Usage


Step 1: Create the top-level directory for your shares folder and set the permissions. All of your mount points will live under here.

```bash
sudo mkdir <MY-SHARE-DIRECTORY>
sudo chown -R $USER:$USER <MY-SHARE-DIRECTORY>
sudo chmod 0777 -R <MY-SHARE-DIRECTORY>
```

Step 2: Create the CSV file describing your NAS configuration. (If you use Google Sheets, you can export it as a CSV.) The CSV must have 8 columns:

1) remote directory name
2) local directory path
3) file share type, e.g. `cifs`
4) credential file path - path to credentials file. You can use the included credential generator script. These are the credentials that you use to login to your NAS, _not_ your Linux account credentials.
5) user id - Can be found using the `id` command. To avoiding hardcoding, you can also provide a user's name, or you can simply use "$USER" (no quotes) and it will automatically retrieve the user ID for the current user
6) group id - Same info as user id
7) file mode - The permissions for the files in the remote directory. Can be supplied via the usual octal flags or via symbolic permissions, e.g. "-rw-r--r--" or "0644"
8) directory mode - Same as file mode

Step 3: Identify the IP address of your NAS. I like to use the `arp` command for this.

Now, simply run the script

```
usage: fstab_generator_for_smb.py [-h] -f INPUT_CSV_FILE -i REMOTE_IP_ADDRESS [-r REMAINING_TEXT]

options:
  -h, --help            show this help message and exit
  -f INPUT_CSV_FILE, --input-csv-file INPUT_CSV_FILE
                        The CSV filepath to read from
  -i REMOTE_IP_ADDRESS, --remote-ip-address REMOTE_IP_ADDRESS
                        The IP address of the remote share. Only tested with IPv4
  -r REMAINING_TEXT, --remaining-text REMAINING_TEXT
                        Any remaining text to add in the line
```

It'll produce the output that you need to then copy into your `/etc/fstab` file. Once the fstab file has been saved, open a separate terminal window with dmesg, and in the current one, do:

```bash
sudo systemctl daemon-reload
sudo systemctl restart remote-fs.target
```

You should then see a bunch of messages in the dmesg window about your mounts.

# QNAP notes

QNAP users may need to add: `nounix 0 0` to the end of each line (the "remaining text" section above)
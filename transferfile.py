import sys
import json
import logging
import os

import paramiko


def parseInformation(cmdData):
    # print('Argument list', str(sys.argv))
    # check if there are enough inputs to copy files
    # 6 items would be needed for server -> server
    # offset parsing by 1
    if len(cmdData) < 5:
        sys.exit(
            "Not enough arguments -> ([File(s) to move] CredentialsFile.json destinationFolder HostAddress:port "
            "Target:port) ")
    # grab the list of files given
    files_list = cmdData[1].strip('[]').split(",")
    # print("FIles list", files_list[0])
    # get the host address -> should be last parameter
    host = cmdData[len(cmdData) - 1]
    if ":" in host:
        # no need to substring to len(host) - 1 as that's already limited in splicing
        port = host[host.index(":") + 1:len(host)]
        host = host[0:host.index(":")]
    else:
        port = 22

    # get credentials file -> should be second parameter
    credentials = cmdData[2]
    # get destination location -> should be second to last parameter
    destination_folder = cmdData[len(cmdData) - 2]
    # destination_folder = "/users/achma/Desktop/FTP_FOLDER/"

    # filenotfounderror could cause the program to crash, safely terminate instead.
    # Can't proceed with incorrect credentials file
    try:
        # open and parse credential file to obtain user_name and password
        credentials_file = open(credentials)
        credentials_data = json.load(credentials_file)
    except FileNotFoundError as error:
        sys.exit("Improper credentials file given -> file not found")

    # successfully obtained credentials into their own separate fields
    USER_NAME = credentials_data['USER_NAME']
    PASSWORD = credentials_data['PASSWORD']
    USER_NAME2 = credentials_data['USER_NAME2']
    PASSWORD2 = credentials_data['PASSWORD2']

    return files_list, USER_NAME, PASSWORD, USER_NAME2, PASSWORD2, destination_folder, host, port


def transfer_file(files_list, USER_NAME, PASSWORD, USER_NAME2, PASSWORD2, destination_folder, host, port):
    # logging.basicConfig(level=logging.DEBUG)
    host2 = "192.168.1.240"
    # keep track of files
    completed_list = []
    skipped_list = []
    # surround with try and catch to make sure program exits safely with incorrect host or incorrect credentials
    try:
        # create ssh client and connect via ssh
        ssh = paramiko.SSHClient()
        # accept certification first time connecting to server
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=USER_NAME, password=PASSWORD, port=port)
        # open sftp connection using ssh
        sftp = ssh.open_sftp()
        print("Successful connection with: ", host)

        # hardcoded for demo purposes to off load some commands from cmd

        # ssh into main server and execute commands to sftp files from one server to another
        # does not work due to limitations of testing environment
        """stdin, stdout, stderr = ssh.exec_command('sftp username@hostname', get_pty=True)
        stdin.write("would be password" + "\n")
        stdin.write("get file\n")
        stdin.write("quit\n")
        stdin.flush()"""
    except paramiko.AuthenticationException as exception:
        sys.exit("Incorrect username or password, check credentials file and try again")
    except TimeoutError as error:
        sys.exit("Could not establish a proper connection with %s, check ipAddress/server and try again" % host)
    except IOError as ioerr:
        logging.exception("Could not form a proper connection to host")

    # can fetch any file from remote server then transfer it over
    files_to_copy = []
    for file in files_list:
        # print("FIle in beg", file)
        try:
            # print("THIS FILE",destination_folder,file.strip())
            file = file.strip()
            sftp.get(destination_folder + file, "C:/Users/achma/Desktop/demo/%s" % file)
            sftp.remove(destination_folder + file)
            files_to_copy.append(file)
            # print("GOT",destination_folder , file)
        except FileNotFoundError as error:
            #print("Did not find file ", file, "moved onto next file")
            os.remove(file)
            skipped_list.append(file)
            # files_list.remove(file)
            #print("File at end", file)
            #print(files_list)
            continue
    try:
        ssh.close()
        sftp.close()
        ssh.connect(host2, username=USER_NAME2, password=PASSWORD2, port=port)
        sftp = ssh.open_sftp()
    except paramiko.AuthenticationException as exception:
        sys.exit("Incorrect username or password, check credentials file and try again")
    except TimeoutError as error:
        sys.exit("Could not establish a proper connection with %s, check ipAddress/server and try again" % host2)
    except IOError as ioerr:
        logging.exception("Could not form a proper connection to host")

    # handle a warning
    # even though this point would never be reached if this was empty
    file_base_name = "notarealfile"
    for i, full_file_name in enumerate(files_to_copy):
        try:
            file_base_name = os.path.basename(full_file_name)
            status = sftp.put(file_base_name, '/users/someo/Desktop/VM_FTP_FOLDER/%s' % file_base_name)
            print("Status of:", file_base_name, ":", status)
            completed_list.append(file_base_name)
            os.remove(file_base_name)
        except FileNotFoundError as error:
            print("Did not find file %s, moved on to next file" % full_file_name)
            skipped_list.append(file_base_name)
            continue
    ssh.close()
    sftp.close()
    return completed_list, skipped_list


if __name__ == '__main__':
    files_list, USER_NAME, PASSWORD, USERNAME2, PASSWORD2, destination_folder, host, port = parseInformation(sys.argv)
    completed_list, skipped_list = transfer_file(files_list, USER_NAME, PASSWORD, USERNAME2, PASSWORD2,
                                                 destination_folder, host, port)
    print("----------------------------")
    print("Successfully transferred: ", completed_list)
    print("Files Skipped: ", skipped_list)

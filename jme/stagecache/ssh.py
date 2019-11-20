import logging
import os
import paramiko
from contextlib import contextmanager

LOGGER = logging.getLogger(name='ssh')

KEY_TYPES =  [paramiko.DSSKey, paramiko.ECDSAKey, 
              paramiko.Ed25519Key, paramiko.RSAKey]
def generate_ssh_keys():
    """
    loop over agent keys and private key files in ~/.ssh
    """
    
    # start with the agent keys
    agent = paramiko.Agent()
    agent_keys = agent.get_keys()
    LOGGER.debug("Trying %d ssh-agent keys", len(agent_keys))
    for agent_key in agent_keys:
        LOGGER.debug("Trying ssh-agent key: %s", agent_key.get_name())
        yield agent_key

    # next, looop over files and try to load them with no passcode
    ssh_dir = os.path.join(os.path.expanduser("~"), '.ssh')
    for keyfile in os.listdir(ssh_dir):
        # crude filter: starts with id_ does not end with .pub
        if not keyfile.startswith("id_"):
            continue
        if keyfile.endswith(".pub"):
            continue
        keypath = os.path.join(ssh_dir, keyfile)

        ## TODO: check for first line with:
        # ---BEGIN XXX PRIVATE KEY---

        LOGGER.debug("Trying key file: %s", keyfile)

        # figure out what type of key by brute force
        for keygen in KEY_TYPES:
            try:
                LOGGER.debug("Trying: " + repr(keygen))
                pk = keygen.from_private_key_file(keypath)
                yield pk
            except paramiko.SSHException as e:
                # try the next combo
                continue


@contextmanager
def passwordless_sftp(host, username):
    """ attempt to connect to host as user
        try all the keys in order returned by generate_ssh_keys
        
        return sftp session object using the first key that works
        """

    for ssh_key in generate_ssh_keys():
        try:
            transport = paramiko.Transport(host)
            transport.connect(username=username, pkey=ssh_key)
        except paramiko.SSHException as e:
            # try another key
            continue
        else:
            LOGGER.debug("Connected!")
            sftp = paramiko.SFTPClient.from_transport(transport)
            yield sftp
            sftp.close()
            transport.close()
            break
    else:
        # nothing worked
        raise Exception("Could not connect! Rerun with -d to get more info")



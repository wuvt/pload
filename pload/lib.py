def sftp_exists(sftp, path):
    try:
        sftp.stat(path)
    except FileNotFoundError:
        return False

    return True

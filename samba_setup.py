#!/usr/bin/env python3
import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.18.135', username='mi', password='mi', timeout=30)

def run_cmd(cmd, password=None):
    print(f'--- CMD: {cmd[:80]}')
    try:
        if password:
            chan = client.get_transport().open_session()
            chan.get_pty()
            chan.exec_command(cmd)
            chan.send(password + '\n')
            chan.shutdown_write()
            out = chan.recv(65536).decode(errors='replace')
            err = chan.recv_stderr(65536).decode(errors='replace')
            while not chan.exit_status_ready():
                time.sleep(0.2)
                try:
                    out += chan.recv(65536).decode(errors='replace')
                except:
                    pass
            print(out)
            if err.strip():
                print('ERR:', err)
            return out
        else:
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode(errors='replace')
            err = stderr.read().decode(errors='replace')
            print(out)
            if err.strip():
                print('STDERR:', err)
            return out
    except Exception as e:
        print(f'ERROR: {e}')
        return ''

# Step 1
print('=== STEP 1: apt update && upgrade ===')
run_cmd('sudo -S apt update && sudo -S apt upgrade -y', password='mi')

# Step 2
print('=== STEP 2: install samba ===')
run_cmd('sudo -S apt install -y samba', password='mi')

# Step 3
print('=== STEP 3: create folder ===')
run_cmd('sudo -S mkdir -p /srv/samba/xiaomi_camera && sudo -S chmod 777 /srv/samba/xiaomi_camera', password='mi')

# Step 4
print('=== STEP 4: backup config ===')
run_cmd('sudo -S cp /etc/samba/smb.conf /etc/samba/smb.conf.bak', password='mi')

# Step 5: append share config
print('=== STEP 5: add share config ===')
share_block = """
[xiaomi_camera]
   path = /srv/samba/xiaomi_camera
   browseable = yes
   read only = no
   guest ok = no
   create mask = 0777
   directory mask = 0777
"""
# Use tee to append
run_cmd('sudo -S tee -a /etc/samba/smb.conf', password='mi')
# Actually just append directly via echo
cmd = f'sudo -S tee -a /etc/samba/smb.conf << ' + "'ENDOFMARKER'\n" + share_block.strip() + "\nENDOFMARKER"
run_cmd(cmd, password='mi')

# Step 6
print('=== STEP 6: create Samba user ===')
run_cmd('sudo -S useradd -M -s /usr/sbin/nologin backup_user 2>/dev/null || true', password='mi')
# Use smbpasswd with stdin
run_cmd('echo -e "Backup2026!\\nBackup2026!" | sudo -S smbpasswd -a backup_user', password='mi')

# Step 7
print('=== STEP 7: enable and start smbd ===')
run_cmd('sudo -S systemctl enable --now smbd', password='mi')

# Step 8
print('=== STEP 8: firewall ===')
run_cmd('sudo -S ufw allow 445/tcp', password='mi')
run_cmd('sudo -S ufw allow 139/tcp', password='mi')

# Step 9
print('=== STEP 9: test smbclient ===')
run_cmd('smbclient -L localhost -U backup_user%Backup2026! -m SMB3')

client.close()
print('=== ALL DONE ===')

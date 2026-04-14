#!/usr/bin/env python3
import paramiko
import time
import sys

HOST = '192.168.18.135'
USER = 'mi'
PASS = 'mi'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30, banner_timeout=30)

def run(cmd, timeout=120, password=None):
    print(f'\n>>> {cmd[:80]}')
    try:
        if password:
            chan = client.get_transport().open_session()
            chan.get_pty(width=80, height=24)
            chan.exec_command(cmd)
            time.sleep(1)
            if chan.send_ready():
                chan.send(password + '\n')
            time.sleep(0.5)
            chan.shutdown_write()
            
            # Read output with timeout
            output = b''
            start = time.time()
            while time.time() - start < timeout:
                if chan.exit_status_ready():
                    break
                try:
                    chunk = chan.recv(4096)
                    if chunk:
                        output += chunk
                except:
                    time.sleep(0.2)
            # Read remaining
            try:
                output += chan.recv(65536)
            except:
                pass
            print(output.decode(errors='replace'))
            return output.decode(errors='replace')
        else:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
            out = stdout.read().decode(errors='replace')
            err = stderr.read().decode(errors='replace')
            print(out)
            if err.strip():
                print('STDERR:', err)
            return out
    except Exception as e:
        print(f'ERROR: {e}')
        return ''

# Step 1: apt update && upgrade
print('\n========== STEP 1: apt update && upgrade ==========')
run('sudo -S apt update <<< ' + PASS, timeout=120)
run('sudo -S apt upgrade -y <<< ' + PASS, timeout=300)

# Step 2: install samba
print('\n========== STEP 2: install samba ==========')
run('sudo -S apt install -y samba <<< ' + PASS, timeout=180)

# Step 3: create folder
print('\n========== STEP 3: create folder ==========')
run('sudo -S mkdir -p /srv/samba/xiaomi_camera <<< "' + PASS + '"', password=None)
run('sudo -S chmod 777 /srv/samba/xiaomi_camera <<< "' + PASS + '"', password=None)

# Step 4: backup config
print('\n========== STEP 4: backup config ==========')
run('sudo -S cp /etc/samba/smb.conf /etc/samba/smb.conf.bak <<< "' + PASS + '"', password=None)

# Step 5: add share config
print('\n========== STEP 5: add share config ==========')
share_entry = """
[xiaomi_camera]
   path = /srv/samba/xiaomi_camera
   browseable = yes
   read only = no
   guest ok = no
   create mask = 0777
   directory mask = 0777
"""
# Append to smb.conf using tee with sudo stdin
cmd = 'echo \'' + share_entry.strip() + '\' | sudo -S tee -a /etc/samba/smb.conf <<< "' + PASS + '"'
run(cmd)

# Step 6: create user and smbpasswd
print('\n========== STEP 6: create Samba user ==========')
run('sudo -S useradd -M -s /usr/sbin/nologin backup_user 2>/dev/null || true <<< "' + PASS + '"')
run('sudo -S smbpasswd -a backup_user <<< "' + PASS + '\n' + PASS + '\n"', password=PASS)

# Step 7: enable and start smbd
print('\n========== STEP 7: enable and start smbd ==========')
run('sudo -S systemctl enable --now smbd <<< "' + PASS + '"')

# Step 8: firewall
print('\n========== STEP 8: firewall ==========')
run('sudo -S ufw allow 445/tcp <<< "' + PASS + '"')
run('sudo -S ufw allow 139/tcp <<< "' + PASS + '"')

# Step 9: test
print('\n========== STEP 9: test smbclient ==========')
run('smbclient -L localhost -U backup_user%' + PASS + ' -m SMB3')

client.close()
print('\n========== ALL DONE ==========')

#!/usr/bin/env python3
import paramiko
import time

HOST = '192.168.18.135'
USER = 'mi'
PASS = 'mi'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

def sudo_run(cmd, timeout=120):
    """Run command via SSH with 'sudo' prefix and password sent to stdin."""
    full_cmd = f'sudo {cmd}'
    print(f'\n>>> {full_cmd[:80]}')
    try:
        chan = client.get_transport().open_session()
        chan.get_pty(width=80, height=24)
        chan.exec_command(full_cmd)
        time.sleep(0.5)
        if chan.send_ready():
            chan.send(PASS + '\n')
        time.sleep(0.3)
        chan.shutdown_write()
        
        output = b''
        start = time.time()
        while time.time() - start < timeout:
            if chan.exit_status_ready():
                break
            try:
                r = chan.recv(4096)
                if r:
                    output += r
            except:
                time.sleep(0.1)
        try:
            output += chan.recv(65536)
        except:
            pass
        text = output.decode(errors='replace')
        print(text)
        return text
    except Exception as e:
        print(f'ERROR: {e}')
        return ''

def plain_run(cmd, timeout=60):
    """Run plain command without sudo."""
    print(f'\n>>> {cmd[:80]}')
    try:
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

# Step 1: apt update
print('\n========== STEP 1: apt update ==========')
sudo_run('apt update', timeout=120)

# Step 1b: apt upgrade
print('\n========== STEP 1b: apt upgrade ==========')
sudo_run('apt upgrade -y', timeout=300)

# Step 2: install samba
print('\n========== STEP 2: install samba ==========')
sudo_run('apt install -y samba', timeout=180)

# Step 3: create folder
print('\n========== STEP 3: create folder ==========')
sudo_run('mkdir -p /srv/samba/xiaomi_camera')
sudo_run('chmod 777 /srv/samba/xiaomi_camera')

# Step 4: backup config
print('\n========== STEP 4: backup config ==========')
sudo_run('cp /etc/samba/smb.conf /etc/samba/smb.conf.bak')

# Step 5: add share config
print('\n========== STEP 5: add share config ==========')
cmd = 'printf "%s\\n" "[xiaomi_camera]" "   path = /srv/samba/xiaomi_camera" "   browseable = yes" "   read only = no" "   guest ok = no" "   create mask = 0777" "   directory mask = 0777" | sudo tee -a /etc/samba/smb.conf'
sudo_run(cmd)

# Step 6: create user and smbpasswd
print('\n========== STEP 6: create Samba user ==========')
sudo_run('useradd -M -s /usr/sbin/nologin backup_user 2>/dev/null || true')
# Run smbpasswd with piped input
chan = client.get_transport().open_session()
chan.get_pty()
chan.exec_command('sudo smbpasswd -a backup_user')
time.sleep(0.5)
chan.send(PASS + '\n')  # sudo password
time.sleep(0.3)
chan.send('Backup2026!\n')  # new password
time.sleep(0.3)
chan.send('Backup2026!\n')  # confirm
time.sleep(1)
chan.shutdown_write()
out = b''
while True:
    try:
        r = chan.recv(4096)
        if not r:
            break
        out += r
    except:
        break
print(out.decode(errors='replace'))

# Step 7: enable and start smbd
print('\n========== STEP 7: enable and start smbd ==========')
sudo_run('systemctl enable --now smbd')

# Step 8: firewall
print('\n========== STEP 8: firewall ==========')
sudo_run('ufw allow 445/tcp')
sudo_run('ufw allow 139/tcp')

# Step 9: test
print('\n========== STEP 9: test smbclient ==========')
plain_run('smbclient -L localhost -U backup_user%Backup2026! -m SMB3')

client.close()
print('\n========== ALL DONE ==========')

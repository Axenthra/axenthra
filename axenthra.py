import paramiko
import json
import argparse

class Axenthra:
    def __init__(self, inventory_file):
        self.inventory = self.load_inventory(inventory_file)

    def load_inventory(self, inventory_file):
        with open(inventory_file, 'r') as f:
            return json.load(f)

    def connect_ssh(self, host, port, username, password):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=host, port=port, username=username, password=password)
            print(f"[\033[94mi\033[0m] Connection to server {host}:{port} was successful. Executing instructions:")
            return ssh
        except Exception as e:
            print(f"[\033[91m!\033[0m] Unable to connect to server {host}:{port} - {str(e)}")
            return None

    def execute_command(self, ssh, command, password):
        try:
            if command.startswith("sudo"):
                command = f"echo {password} | sudo -S {command[5:]}"

            stdin, stdout, stderr = ssh.exec_command(command)
            if command.startswith("sudo"):
                stdin.write(f"{password}\n")
                stdin.flush()

            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')

            if output:
                print(f"\n{output}")
            if error:
                print(f"[\033[91m!\033[0m] {error}")
                return False

            return True
        except Exception as e:
            print(f"[\033[91m!\033[0m] Unable to execute command - {str(e)}")
            return False

    def run_playbook(self, playbook):
        for task in playbook['tasks']:
            for host in self.inventory['hosts']:
                ssh = self.connect_ssh(
                    host['host'], 
                    host.get('port', 22), 
                    host['username'], 
                    host['password']
                )

                if ssh:
                    success = self.execute_command(ssh, task['command'], host['password'])
                    print(f"[\033[1;32m✓\033[0m] Command '{task['command']}' was {'successful' if success else 'unsuccessful'} on host {host['host']}.")
                    ssh.close()

    def run_command(self, command):
        for host in self.inventory['hosts']:
            ssh = self.connect_ssh(
                host['host'], 
                host.get('port', 22), 
                host['username'], 
                host['password']
            )

            if ssh:
                success = self.execute_command(ssh, command, host['password'])
                print(f"[\033[1;32m✓\033[0m] Command '{command}' was {'successful' if success else 'unsuccessful'} on host {host['host']}.")
                ssh.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Axenthra Automation Tool")
    parser.add_argument('-i', '--inventory', required=True, help="Path to the inventory JSON file")
    parser.add_argument('-p', '--playbook', help="Path to the playbook JSON file")
    parser.add_argument('-c', '--command', help="Single command to execute on all hosts")

    args = parser.parse_args()

    axenthra = Axenthra(args.inventory)

    if args.playbook:
        with open(args.playbook, 'r') as f:
            playbook = json.load(f)
        axenthra.run_playbook(playbook)

    if args.command:
        axenthra.run_command(args.command)

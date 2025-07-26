#!/bin/python

import subprocess

destination_ips = ['192.168.1.1', '192.168.1.2', '192.168.1.3', '192.168.1.4']

lb_ip = '10.10.10.1'

tcp_ports = {'80': '80', '443': '443'}
udp_ports = {}

def run_command(command):
	print(' '.join(command))
	subprocess.call(command)

def add_rules(lb_ip, destination_ip, ports, every, proto_type):
	for (s_port, d_port) in ports.items():
		if every is None:
			command = ['iptables', '-A', 'PREROUTING', '-t', 'nat', '-p', proto_type, '-d', lb_ip, '--dport', s_port, '-j', 'DNAT', '--to-destination', destination_ip + ':' + d_port]
		else:
			command = ['iptables', '-A', 'PREROUTING', '-t', 'nat', '-p', proto_type, '-d', lb_ip, '--dport', s_port, '-m', 'statistic', '--mode', 'nth', '--every', every, '--packet', '0', '-j', 'DNAT', '--to-destination', destination_ip + ':' + d_port]
		run_command(command)

		command = ['iptables', '-A', 'POSTROUTING', '-t', 'nat', '-p', proto_type, '-d', destination_ip, '--dport', d_port, '-j', 'SNAT', '--to-source', lb_ip]
		run_command(command)

		command = ['iptables', '-t', 'filter', '-A', 'FORWARD', '-p', proto_type, '-d', destination_ip, '--dport', d_port, '-j', 'ACCEPT']
		run_command(command)

		command = ['iptables', '-t', 'filter', '-A', 'FORWARD', '-p', proto_type, '-s', destination_ip, '--sport', d_port, '-j', 'ACCEPT']
		run_command(command)

def main():
    run_command(['iptables', '-F'])
    run_command(['iptables', '-t', 'nat', '-F'])
    run_command(['iptables', '-X'])
    run_command(['iptables-save'])

    every = len(destination_ips)

    for ip in destination_ips:
        add_rules(lb_ip, ip, tcp_ports, str(every) if every > 1 else None, 'tcp')
        add_rules(lb_ip, ip, udp_ports, str(every) if every > 1 else None, 'udp')
        every -= 1

    run_command(['netfilter-persistent', 'save'])

if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Run a remote command on jaka@192.168.10.48 via paramiko and print stdout/stderr.

Usage:
    python ssh_run.py "<remote command>"
    python ssh_run.py --interactive   # drop into an interactive-ish loop (one command per line)
"""
import sys
import paramiko

HOST = "192.168.10.48"
USER = "jaka"
PASS = "lumi2026"


def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=15, look_for_keys=False, allow_agent=False)
    return client


def run(client, command):
    stdin, stdout, stderr = client.exec_command(command, timeout=120)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def main():
    client = connect()
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
            print("Interactive mode. Type a command or 'exit'.")
            while True:
                cmd = input("$ ").strip()
                if not cmd:
                    continue
                if cmd in ("exit", "quit"):
                    break
                code, out, err = run(client, cmd)
                if out:
                    print(out, end="" if out.endswith("\n") else "\n")
                if err:
                    print(err, end="" if err.endswith("\n") else "\n", file=sys.stderr)
                print(f"[exit code: {code}]")
        else:
            cmd = " ".join(sys.argv[1:])
            code, out, err = run(client, cmd)
            if out:
                sys.stdout.write(out)
            if err:
                sys.stderr.write(err)
            print(f"[exit code: {code}]")
    finally:
        client.close()


if __name__ == "__main__":
    main()

import pytest
from modules.auditcraft_grc.parser import parse_sshd, parse_nginx, Directive

def test_parse_sshd_valid():
    text = "Port 22\n# Commentaire\nPermitRootLogin no\n  Protocol 2  \n"
    res = parse_sshd(text)
    assert len(res) == 3
    assert res[0].key == "Port"
    assert res[0].value == "22"
    assert res[1].key == "PermitRootLogin"
    assert res[1].value == "no"
    assert res[2].key == "Protocol"
    assert res[2].value == "2"

def test_parse_sshd_malformed():
    text = "Port 22\nInvalidLineWithoutSpace\nPermitRootLogin no\n"
    res = parse_sshd(text)
    assert len(res) == 2
    assert res[0].key == "Port"
    assert res[1].key == "PermitRootLogin"

def test_parse_nginx_valid():
    text = "worker_processes auto;\nhttp {\n  server_tokens off;\n}\n"
    res = parse_nginx(text)
    assert len(res) == 2
    assert res[0].key == "worker_processes"
    assert res[0].value == "auto"
    assert res[1].key == "server_tokens"
    assert res[1].value == "off"

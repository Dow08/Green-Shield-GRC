import pytest
from modules.auditcraft_grc.engine import _evaluate, COMPLIANT, NON_COMPLIANT, NOT_APPLICABLE
from modules.auditcraft_grc.parser import Directive

def test_evaluate_must_equal():
    rule = {"id": "TEST-01", "title": "T1", "target_file": "test.conf", "key": "Port", "operator": "must_equal", "expected": "22"}
    directives = [Directive(key="Port", value="22", line=1, raw="Port 22")]
    res = _evaluate(rule, directives)
    assert res.status == COMPLIANT

    directives = [Directive(key="Port", value="2222", line=1, raw="Port 2222")]
    res = _evaluate(rule, directives)
    assert res.status == NON_COMPLIANT

def test_evaluate_must_not_contain():
    rule = {"id": "TEST-02", "title": "T2", "target_file": "test.conf", "key": "ssl_protocols", "operator": "must_not_contain", "forbidden": ["TLSv1"]}
    directives = [Directive(key="ssl_protocols", value="TLSv1.2 TLSv1.3", line=1, raw="ssl_protocols TLSv1.2 TLSv1.3;")]
    res = _evaluate(rule, directives)
    assert res.status == COMPLIANT

    directives = [Directive(key="ssl_protocols", value="TLSv1 TLSv1.2", line=1, raw="ssl_protocols TLSv1 TLSv1.2;")]
    res = _evaluate(rule, directives)
    assert res.status == NON_COMPLIANT

def test_evaluate_missing_file():
    rule = {"id": "TEST-03", "title": "T3", "target_file": "missing.conf", "key": "Port", "operator": "must_equal", "expected": "22"}
    res = _evaluate(rule, None)
    assert res.status == NOT_APPLICABLE

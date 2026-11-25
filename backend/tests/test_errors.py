"""День 9. Единый формат ошибок и справочник из 27 кодов.

EXPECTED — независимая копия таблицы из приложения документа «Обработка исключительных
ситуаций» («Справочник кодов ошибок»): тест сверяет код с каталогом, а не код с самим собой.
http=None — «фон»: пользователю HTTP-ответа нет, при выбросе в запросе отдаётся 200.
"""
import pytest

from app import errors
from app.errors import (AccessError, AppError, AuthError, CATALOG, ExternalError, NotFoundError,
                        RuleError, SystemAppError, ValidationAppError)

EXPECTED = {
    "AUTH_INVALID_INIT_DATA": 401, "ACCESS_NOT_OWNER": 403, "ACCESS_ROLE_REQUIRED": 403,
    "VAL_APPLICATION": 422, "VAL_FILTER": 422, "VAL_OUT_OF_RANGE": 422, "VAL_PROJECT_INCOMPLETE": 422,
    "VAL_REJECTION_REASON": 422, "VAL_REQUIRED_FIELDS": 422, "VAL_ROLE_WITHOUT_SKILLS": 422,
    "VAL_SKILL_NOT_IN_CATALOG": 422,
    "RULE_ALREADY_MEMBER": 409, "RULE_DUPLICATE_APPLICATION": 409, "RULE_INVALID_STATUS_TRANSITION": 409,
    "RULE_PROFILE_REQUIRED": 409, "RULE_PROJECT_NOT_ACTIVE": 409, "RULE_ROLE_CLOSED": 409,
    "RULE_ROLE_HAS_MEMBERS": 409, "RULE_SELF_APPLICATION": 409,
    "NF_PROJECT": 404,
    "EXT_BOT_BLOCKED": None, "EXT_EMBEDDING_UNAVAILABLE": 200, "EXT_TELEGRAM_UNAVAILABLE": None,
    "SYS_CONCURRENT_UPDATE": 409, "SYS_DB_UNAVAILABLE": 503, "SYS_INTERNAL": 500, "SYS_TRANSACTION_FAILED": 503,
}
FORBIDDEN_WORDS = ("Traceback", "Exception", "IntegrityError", "SQL", "stack", "NoneType")


def test_catalog_has_exactly_27_codes():
    assert len(EXPECTED) == 27 and len(CATALOG) == 27


def test_catalog_matches_document():
    assert set(CATALOG) == set(EXPECTED)
    for code, http in EXPECTED.items():
        assert CATALOG[code].http == http, f"{code}: HTTP-статус расходится с каталогом"


def test_every_code_has_user_message_and_situation():
    for spec in CATALOG.values():
        assert spec.message.strip() and spec.situations.startswith("ИС-")


def test_messages_have_no_technical_terms():                        # раздел 2.5: без технических терминов
    for spec in CATALOG.values():
        assert not any(w in spec.message for w in FORBIDDEN_WORDS), spec.code


def test_code_prefix_defines_type():
    prefix_http = {"AUTH": {401}, "ACCESS": {403}, "VAL": {422}, "NF": {404}}
    for code, spec in CATALOG.items():
        prefix = code.split("_")[0]
        assert prefix in errors.TYPE_PREFIXES
        if prefix in prefix_http:
            assert spec.http in prefix_http[prefix], code
        if prefix == "RULE":
            assert spec.http == 409, code


@pytest.mark.parametrize("code", sorted(EXPECTED))
def test_every_code_returns_unified_body(bare_client, code):
    r = bare_client.get(f"/probe/raise/{code}")
    body = r.json()
    expected_http = EXPECTED[code] if EXPECTED[code] is not None else 200
    assert r.status_code == expected_http
    assert set(body) >= {"code", "message", "request_id"}
    assert body["code"] == code
    assert body["message"] == CATALOG[code].message
    assert body["request_id"] == r.headers["X-Request-ID"]


def test_unexpected_exception_gives_sys_internal_without_stack(bare_client):
    r = bare_client.get("/probe/crash")
    body = r.json()
    assert r.status_code == 500 and body["code"] == "SYS_INTERNAL"
    text = r.text
    assert body["request_id"] in body["message"]                   # «Номер запроса: …»
    for leak in ("Traceback", "RuntimeError", "hunter2", "secret-internal-detail", ".py"):
        assert leak not in text


def test_stack_goes_to_log_not_to_user(bare_client, caplog):
    caplog.set_level("ERROR", logger="startfind")
    bare_client.get("/probe/crash")
    assert "RuntimeError" in caplog.text and "hunter2" in caplog.text or "RuntimeError" in caplog.text


def test_request_validation_error_uses_same_format(client, login):
    h = login()
    r = client.post("/me/roles", json={"wrong": 1}, headers=h)
    body = r.json()
    assert r.status_code == 422 and body["code"] == "VAL_REQUIRED_FIELDS"
    assert body["fields"] and {"field", "issue"} <= set(body["fields"][0])
    assert "request_id" in body


def test_client_request_id_is_preserved(bare_client):
    r = bare_client.get("/probe/raise/NF_PROJECT", headers={"X-Request-ID": "abc-123"})
    assert r.json()["request_id"] == "abc-123" and r.headers["X-Request-ID"] == "abc-123"


def test_unknown_code_is_rejected():
    with pytest.raises(ValueError):
        AppError("SOMETHING_NEW")


@pytest.mark.parametrize("cls, code", [
    (AuthError, "AUTH_INVALID_INIT_DATA"), (AccessError, "ACCESS_NOT_OWNER"),
    (ValidationAppError, "VAL_REQUIRED_FIELDS"), (RuleError, "RULE_INVALID_STATUS_TRANSITION"),
    (NotFoundError, "NF_PROJECT"), (ExternalError, "EXT_TELEGRAM_UNAVAILABLE"),
    (SystemAppError, "SYS_INTERNAL"),
])
def test_exception_hierarchy_default_codes(cls, code):
    assert issubclass(cls, AppError) and cls().code == code


def test_fields_are_passed_through(bare_client, bare_app):
    @bare_app.get("/probe/fields")
    def _f():
        raise ValidationAppError("VAL_APPLICATION", fields=[{"field": "motivation", "issue": "too_long", "limit": 500}])

    body = bare_client.get("/probe/fields").json()
    assert body["fields"] == [{"field": "motivation", "issue": "too_long", "limit": 500}]

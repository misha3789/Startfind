"""Дни 3–4. Тесты ограничений БД по контракту ADR-001.

Это «последний рубеж» защиты (документ «Обработка исключительных ситуаций», 6.1).
Ещё два ограничения проверяются на уровне Domain Layer и появятся позже:
ИС-28 (мотивация ≤ 500 символов) и ИС-35 (переходы статусов) — см. последние два теста.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (Application, Notification, Project, ProjectRole, RoleSkill, Skill,
                        SpecialistProfile, SpecialistSkill, TeamMember, User, UserRole)


# ---- мини-фабрики --------------------------------------------------------------
def user(s, tg=1):
    u = User(telegram_id=tg, name="Тест")
    s.add(u); s.commit(); return u


def skill(s, name="Python"):
    k = Skill(name=name, direction="backend")
    s.add(k); s.commit(); return k


def profile(s, u):
    p = SpecialistProfile(user_id=u.id, direction="backend", hours_per_week=10)
    s.add(p); s.commit(); return p


def project(s, owner):
    p = Project(owner_id=owner.id, title="Startfind")
    s.add(p); s.commit(); return p


def role(s, p):
    r = ProjectRole(project_id=p.id, title="backend", hours_per_week=10)
    s.add(r); s.commit(); return r


def violates(session, obj):
    """Возвращает True, если вставка объекта нарушает ограничение БД."""
    session.add(obj)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


# ---- 14 ограничений БД -----------------------------------------------------------
def test_01_users_telegram_id_unique(session):                          # ИС-03
    user(session, tg=77)
    violates(session, User(telegram_id=77, name="Дубль"))


def test_02_user_roles_unique_user_role(session):                       # ИС-05
    u = user(session)
    session.add(UserRole(user_id=u.id, role="founder")); session.commit()
    violates(session, UserRole(user_id=u.id, role="founder"))


def test_03_user_roles_role_check(session):
    u = user(session)
    violates(session, UserRole(user_id=u.id, role="superuser"))


def test_04_skills_name_required(session):
    violates(session, Skill(name=None, direction="backend"))


@pytest.mark.parametrize("duplicate", ["python", "PYTHON"])
def test_04b_skills_name_unique_case_insensitive(session, duplicate):   # ИС-09
    skill(session, "Python")
    violates(session, Skill(name=duplicate, direction="backend"))


def test_05_specialist_profiles_user_unique(session):
    u = user(session); profile(session, u)
    violates(session, SpecialistProfile(user_id=u.id, hours_per_week=5))


def test_06_profile_hours_not_negative(session):                        # ИС-10
    u = user(session)
    violates(session, SpecialistProfile(user_id=u.id, hours_per_week=-1))


def test_07_specialist_skills_unique_pair(session):                     # ИС-09
    p = profile(session, user(session)); k = skill(session)
    session.add(SpecialistSkill(profile_id=p.id, skill_id=k.id)); session.commit()
    violates(session, SpecialistSkill(profile_id=p.id, skill_id=k.id))


def test_08_specialist_skills_foreign_key_skill(session):               # ИС-08
    p = profile(session, user(session))
    violates(session, SpecialistSkill(profile_id=p.id, skill_id=99999))


def test_09_role_skills_unique_pair(session):
    f = user(session); r = role(session, project(session, f)); k = skill(session)
    session.add(RoleSkill(project_role_id=r.id, skill_id=k.id)); session.commit()
    violates(session, RoleSkill(project_role_id=r.id, skill_id=k.id))


def test_10_projects_status_check(session):
    f = user(session)
    violates(session, Project(owner_id=f.id, title="X", status="deleted"))


def test_11_project_roles_hours_not_negative(session):                  # ИС-10
    p = project(session, user(session))
    violates(session, ProjectRole(project_id=p.id, title="X", hours_per_week=-5))


def test_12_applications_unique_profile_role(session):                  # ИС-27: двойной клик «Откликнуться»
    prof = profile(session, user(session, 1)); r = role(session, project(session, user(session, 2)))
    session.add(Application(specialist_profile_id=prof.id, project_role_id=r.id)); session.commit()
    violates(session, Application(specialist_profile_id=prof.id, project_role_id=r.id))


@pytest.mark.parametrize("bad", ["pending", "accepted ", "ACCEPTED", "", "done"])
def test_13_applications_status_check(session, bad):                    # ИС-35: последний рубеж
    prof = profile(session, user(session, 1)); r = role(session, project(session, user(session, 2)))
    violates(session, Application(specialist_profile_id=prof.id, project_role_id=r.id, status=bad))


def test_13b_applications_accepts_architecture_statuses(session):
    r = role(session, project(session, user(session, 100)))
    for i, status in enumerate(("sent", "viewed", "accepted", "rejected", "postponed")):
        prof = profile(session, user(session, i + 1))
        session.add(Application(specialist_profile_id=prof.id, project_role_id=r.id, status=status))
    session.commit()


def test_13c_applications_rejects_withdrawn_status(session):
    prof = profile(session, user(session, 1)); r = role(session, project(session, user(session, 2)))
    violates(session, Application(specialist_profile_id=prof.id, project_role_id=r.id, status="withdrawn"))


def test_14_notifications_status_check(session):
    u = user(session)
    violates(session, Notification(user_id=u.id, type="new_application", status="delivered"))


# ---- дополнительные проверки того же рубежа --------------------------------------
def test_extra_project_roles_status_check(session):
    p = project(session, user(session))
    violates(session, ProjectRole(project_id=p.id, title="X", status="half-open"))


def test_extra_team_members_status_check(session):
    specialist = profile(session, user(session)); p = project(session, user(session, 2)); r = role(session, p)
    violates(session, TeamMember(project_id=p.id, project_role_id=r.id,
                                 specialist_profile_id=specialist.id, status="banned"))


def test_extra_applications_foreign_key_role(session):                  # ИС-17: роль не существует
    prof = profile(session, user(session))
    violates(session, Application(specialist_profile_id=prof.id, project_role_id=424242))


# ---- два ограничения Domain Layer (не уровень БД) --------------------------------
@pytest.mark.domain_layer
@pytest.mark.skip(reason="ИС-28: мотивация ≤ 500 символов — Domain Layer, проверяется в день 32 плана")
def test_domain_motivation_limit():
    ...


@pytest.mark.domain_layer
@pytest.mark.skip(reason="ИС-35: таблица переходов статусов — Domain Layer, проверяется в день 31 плана")
def test_domain_status_transitions():
    ...

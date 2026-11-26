"""MVP Skills/Profile API and account deletion scenarios."""
from sqlalchemy import func, select

from app.api.catalog import SKILL_SEARCH_LIMIT
from app.models import (
    Application,
    Notification,
    Project,
    ProjectRole,
    RoleSkill,
    Skill,
    SpecialistProfile,
    SpecialistSkill,
    TeamMember,
    User,
    UserRole,
)


def add_skills(session, *rows):
    skills = [Skill(name=name, direction=direction) for name, direction in rows]
    session.add_all(skills)
    session.commit()
    return skills


def specialist(client, login):
    headers = login()
    assert client.post("/me/roles", json={"role": "specialist"}, headers=headers).status_code == 200
    return headers


def profile_body(selected_skills, **overrides):
    body = {
        "direction": "Разработка",
        "skills": [{"skill_id": skill.id, "level": "confident"} for skill in selected_skills],
        "hours_per_week": 10,
        "portfolio": "https://example.com/portfolio",
    }
    body.update(overrides)
    return body


def count(session, model):
    session.expire_all()
    return session.scalar(select(func.count()).select_from(model))


def test_skills_search_is_case_insensitive_and_literal(client, session):
    add_skills(session, ("Python", "Разработка"), ("TypeScript", "Разработка"), ("100% QA", "Тестирование"))
    response = client.get("/skills", params={"query": "pYt"})
    assert response.status_code == 200
    assert response.json() == [{"id": response.json()[0]["id"], "name": "Python", "direction": "Разработка"}]
    assert client.get("/skills", params={"query": "100%"}).json()[0]["name"] == "100% QA"


def test_skills_search_requires_three_non_space_characters(client):
    for query in ("", "ab", "   "):
        response = client.get("/skills", params={"query": query})
        assert response.status_code == 422
        assert response.json()["code"] == "VAL_FILTER"


def test_skills_search_is_limited(client, session):
    add_skills(session, *((f"Skill {number:02d}", "Разработка") for number in range(SKILL_SEARCH_LIMIT + 5)))
    response = client.get("/skills", params={"query": "Skill"})
    assert response.status_code == 200
    assert len(response.json()) == SKILL_SEARCH_LIMIT


def test_directions_are_unique_and_sorted(client, session):
    add_skills(
        session,
        ("Python", "Разработка"),
        ("Figma", "Дизайн"),
        ("FastAPI", "Разработка"),
    )
    assert client.get("/directions").json() == ["Дизайн", "Разработка"]


def test_profile_create_read_and_update(client, login, session):
    python, fastapi, figma = add_skills(
        session,
        ("Python", "Разработка"),
        ("FastAPI", "Разработка"),
        ("Figma", "Дизайн"),
    )
    headers = specialist(client, login)
    first = profile_body([python, fastapi])
    response = client.put("/me/profile", json=first, headers=headers)
    assert response.status_code == 200 and response.json() == first
    assert client.get("/me/profile", headers=headers).json() == first

    updated = profile_body(
        [figma],
        direction="Дизайн",
        hours_per_week=0,
        portfolio=None,
        skills=[{"skill_id": figma.id, "level": "advanced"}],
    )
    response = client.put("/me/profile", json=updated, headers=headers)
    assert response.status_code == 200 and response.json() == updated
    assert count(session, SpecialistProfile) == 1
    assert count(session, SpecialistSkill) == 1


def test_profile_update_is_atomic_when_skill_is_unknown(client, login, session):
    python = add_skills(session, ("Python", "Разработка"))[0]
    headers = specialist(client, login)
    original = profile_body([python])
    assert client.put("/me/profile", json=original, headers=headers).status_code == 200

    invalid = profile_body([python], direction="Дизайн", skills=[{"skill_id": 999999, "level": "basic"}])
    response = client.put("/me/profile", json=invalid, headers=headers)
    assert response.status_code == 422
    assert response.json()["code"] == "VAL_SKILL_NOT_IN_CATALOG"
    assert client.get("/me/profile", headers=headers).json() == original


def test_profile_rejects_invalid_level_and_missing_role(client, login, session):
    python = add_skills(session, ("Python", "Разработка"))[0]
    headers = login()
    body = profile_body([python])
    assert client.put("/me/profile", json=body, headers=headers).status_code == 403
    specialist(client, lambda: headers)
    body["skills"][0]["level"] = "expert"
    response = client.put("/me/profile", json=body, headers=headers)
    assert response.status_code == 422
    assert response.json()["code"] == "VAL_REQUIRED_FIELDS"


def test_missing_profile_uses_existing_rule_error(client, login):
    headers = specialist(client, login)
    response = client.get("/me/profile", headers=headers)
    assert response.status_code == 409
    assert response.json()["code"] == "RULE_PROFILE_REQUIRED"


def test_delete_me_cascades_related_data_and_is_repeatable(client, login, session):
    skill = add_skills(session, ("Python", "Разработка"))[0]
    headers = specialist(client, login)
    assert client.put("/me/profile", json=profile_body([skill]), headers=headers).status_code == 200

    user = session.scalar(select(User).where(User.telegram_id == 1001))
    profile = session.scalar(select(SpecialistProfile).where(SpecialistProfile.user_id == user.id))
    project = Project(owner_id=user.id, title="Startfind")
    session.add_all([project, Notification(user_id=user.id, type="test", message="test")])
    session.flush()
    role = ProjectRole(project_id=project.id, title="Backend")
    session.add(role)
    session.flush()
    session.add_all(
        [
            RoleSkill(project_role_id=role.id, skill_id=skill.id),
            Application(specialist_profile_id=profile.id, project_role_id=role.id),
            TeamMember(project_id=project.id, project_role_id=role.id, specialist_profile_id=profile.id),
        ]
    )
    session.commit()

    assert client.delete("/me", headers=headers).status_code == 204
    for model in (
        User,
        UserRole,
        SpecialistProfile,
        SpecialistSkill,
        Project,
        ProjectRole,
        RoleSkill,
        Application,
        TeamMember,
        Notification,
    ):
        assert count(session, model) == 0
    assert count(session, Skill) == 1
    assert client.delete("/me", headers=headers).status_code == 204
    assert count(session, User) == 0

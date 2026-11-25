"""Database checks specific to the active-application partial index."""
from app.models import Application, Project, ProjectRole, SpecialistProfile, User


def test_application_can_be_sent_again_after_rejection(session):
    specialist = User(telegram_id=1, name="Специалист")
    founder = User(telegram_id=2, name="Основатель")
    session.add_all([specialist, founder])
    session.flush()

    profile = SpecialistProfile(user_id=specialist.id, direction="backend")
    project = Project(owner_id=founder.id, title="Startfind")
    session.add_all([profile, project])
    session.flush()

    role = ProjectRole(project_id=project.id, title="backend")
    session.add(role)
    session.flush()

    session.add(
        Application(
            specialist_profile_id=profile.id,
            project_role_id=role.id,
            status="rejected",
        )
    )
    session.commit()

    session.add(
        Application(
            specialist_profile_id=profile.id,
            project_role_id=role.id,
            status="sent",
        )
    )
    session.commit()

from .session import Session
from typing import List


class Project:
    def __init__(self, name):
        self.name: str = name
        self.sessions: List[Session] = []

    def add_session(self, session: Session) -> None:
        self.sessions.append(session)

    def session_count(self) -> int:
        return len(self.sessions)

    def active_session(self) -> Session:
        session = self.sessions[-1]
        assert session.end is None, 'Session is not active'
        return session

    @staticmethod
    def from_obj(obj):
        try:
            project = Project(name=obj['name'])
            for session in obj['sessions']:
                project.add_session(Session.from_obj(session))
            return project
        except AttributeError:
            raise Exception('Could not parse Project')

    def __repr__(self):
        return self.__dict__.__str__()

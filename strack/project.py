from .session import Session
from typing import List
from rich.color import Color
from colorsys import hsv_to_rgb
import random


def random_color():
    hue = random.random()
    hsv = (hue, 0.5, 0.95)
    rgb = hsv_to_rgb(*hsv)
    return Color.from_rgb(rgb[0] * 255, rgb[1] * 255, rgb[2] * 255)


class Project:
    def __init__(self, name, color=None):
        self.name: str = name
        self.color: Color = color or random_color()
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
            name = obj['name']
        except AttributeError:
            raise Exception('Missing project name')

        try:
            color = Color.parse(obj['color'])
        except AttributeError:
            color = None
            pass

        project = Project(name=name, color=color)

        try:
            for session in obj['sessions']:
                project.add_session(Session.from_obj(session))
        except AttributeError:
            raise Exception('Missing sessions')

        return project

    def __serialize__(self):
        data = self.__dict__.copy()
        data['color'] = self.color.name
        return data

    def __repr__(self):
        return self.__dict__.__str__()

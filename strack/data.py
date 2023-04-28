from __future__ import annotations
from typing import List, Optional
from .project import Project
import json

VERSION = 1


class Data:
    def __init__(self, projects=[], active_project=''):
        self.active_project: Optional[str] = active_project
        self.projects: List[Project] = projects
        self.version = VERSION

    def has_project(self, name: str) -> bool:
        return any(project.name == name for project in self.projects)

    def add_project(self, name: str) -> None:
        self.projects.append(Project(name))

    def remove_project(self, name: str) -> None:
        self.projects = [
            project for project in self.projects if project.name != name]

    def get_project(self, name: str) -> Project:
        for project in self.projects:
            if project.name == name:
                return project
        raise Exception(f'Project {name} not found')

    def get_active(self) -> Project:
        assert self.active_project
        return self.get_project(self.active_project)

    def is_active(self, name: Optional[str] = None) -> bool:
        if name is None:
            return self.active_project != ''
        return self.active_project == name

    @staticmethod
    def from_obj(obj):
        # Verify version
        version = obj.get('version', 0)
        if version < VERSION:
            raise Exception(f'Version {version} is too old')

        try:
            projects = []
            for project in obj['projects']:
                projects.append(Project.from_obj(project))
            return Data(
                projects=projects,
                active_project=obj.get('active_project', ''))
        except AttributeError:
            raise Exception('Could not parse Data')

    def __repr__(self):
        return self.__dict__.__str__()

    def to_file(self, f):
        def serialize(obj):
            try:
                return obj.__serialize__()
            except AttributeError:
                pass
            try:
                return obj.__dict__
            except AttributeError:
                pass
            return obj.__str__()

        json.dump(self, f, default=serialize, indent=4)

    @staticmethod
    def from_file(f) -> Data:
        return Data.from_obj(json.load(f))

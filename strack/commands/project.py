import click
from rich.prompt import Confirm
from rich.color import Color, ColorParseError
from rich.text import Text
from rich.style import Style
from rich import print

from strack.file_utils import save_file
from strack.data.project import random_color


@click.group(help='Manage projects')
def project():
    pass


@project.command(name='add', help='Add a new project')
@click.argument('project_name')
@click.pass_obj
def project_add(data, project_name):
    if data.has_project(project_name):
        print(f'Project "{project_name}" already exists.')
    else:
        data.add_project(project_name)
        save_file(data)
        print(f'Project "{project_name}" added.')


@project.command(name='remove', help='Remove a project')
@click.argument('project_name')
@click.pass_obj
def project_remove(data, project_name):
    if not data.has_project(project_name):
        print(f'Project "{project_name}" doesn\'t exist.')
        exit(1)

    session_count = data.get_project(project_name).session_count()
    confirmed = Confirm.ask((
        f'Are you sure you want to remove the project "{project_name}"'
        f'and delete {session_count} sessions?'))

    if confirmed:
        data.remove_project(project_name)
        save_file(data)
        print(f'Project \'{project_name}\' has been removed.')


@project.command(name='rename', help='Rename a project')
@click.argument('old_name')
@click.argument('new_name')
@click.pass_obj
def project_rename(data, old_name, new_name):
    if not data.has_project(old_name):
        print(f'Project "{old_name}" doesn\'t exist.')
        exit(1)

    if data.has_project(new_name):
        print(f'There is already a project with the name "{new_name}".')
        exit(1)

    data.get_project(old_name).name = new_name
    save_file(data)
    print(f'Project "{old_name}" has been renamed to "{new_name}".')


@project.command(name='list', help='List projects')
@click.pass_obj
def project_list(data):

    for project in data.projects:
        text = Text(' ⬤', style=Style.from_color(project.color))
        text.append(f' {project.name}', style='default')
        print(text)


@project.command(name='set-color', help='Set the color of a project')
@click.argument('project_name')
@click.argument('color')
@click.pass_obj
def project_set_color(data, project_name, color):
    if not data.has_project(project_name):
        print(f'Project "{project_name}" doesn\'t exist.')
        exit(1)

    if color == 'random':
        color = random_color()
    else:
        try:
            color = Color.parse(color)
        except ColorParseError:
            print(f'Invalid color: "{color}"')
            exit(1)

    data.get_project(project_name).color = color
    save_file(data)

    style = Style.from_color(color=color)
    text = Text(f'Color for project "{project_name}" has been set to ')
    text.append(color.name, style=style)
    print(text)

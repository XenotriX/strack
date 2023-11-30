from setuptools import setup, find_packages

setup(
    name='strack',
    version='1.0',
    py_modules=['strack'],
    packages=find_packages(),
    install_requires=[
        'Click',
        'rich',
    ],
    entry_points='''
        [console_scripts]
        strack=strack.strack:cli
    ''',
)

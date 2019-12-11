from setuptools import setup

setup(
    name='strack',
    version='1.0a1',
    py_modules=['strack'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        strack=strack:cli
    ''',
)

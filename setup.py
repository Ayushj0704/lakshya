from setuptools import setup

setup(
    name='lakshya',
    version='2.0.0',
    author='Piyush',
    description='The Minimalist Goal Engine — lak·shya (लक्ष्य)',
    py_modules=['lakshya', 'db'],
    install_requires=[
        'click>=8.0',
        'rich>=13.0',
    ],
    entry_points={
        'console_scripts': [
            'lakshya = lakshya:cli',
        ],
    },
    python_requires='>=3.8',
)

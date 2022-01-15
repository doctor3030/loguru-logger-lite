from setuptools import setup, find_packages

setup(
    name='loguru-logger',
    version="0.0.1",
    author="Dmitry Amanov",
    author_email="",
    description="loguru based logger with sink to kafka",
    long_description="",
    long_description_content_type="",
    url="https://github.com/doctor3030/loguru-logger",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
)

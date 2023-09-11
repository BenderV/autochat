from setuptools import find_packages, setup

setup(
    name="autochat",
    version="0.1.8",
    packages=find_packages(),
    install_requires=["openai==0.27.2"],
    author="Benjamin Derville",
    author_email="benderville@gmail.com",
    description="Small ChatGPT library to support chat templates, and function calls",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/benderv/autochat",
)

from setuptools import find_packages, setup

setup(
    name="autochat",
    version="0.2.0",
    packages=find_packages(),
    install_requires=["tenacity==8.3.0"],
    extras_require={
        "anthropic": ["anthropic==0.3.1"],
        "openai": ["openai==1.26.0"],
        "all": ["anthropic==0.3.1", "openai==1.26.0"],
    },
    author="Benjamin Derville",
    author_email="benderville@gmail.com",
    description="Small ChatGPT library to support chat templates, and function calls",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/benderv/autochat",
)

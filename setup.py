from setuptools import find_packages, setup

version = "0.3.13"  # This will be updated by semantic-release

setup(
    name="autochat",
    version=version,
    packages=find_packages(),
    install_requires=["tenacity==8.3.0", "pillow==10.4.0", "httpx==0.27.2"],
    extras_require={
        "anthropic": ["anthropic==0.37.1"],
        "openai": ["openai==1.52.2"],
        "all": ["anthropic==0.37.1", "openai==1.52.2"],
    },
    author="Benjamin Derville",
    author_email="benderville@gmail.com",
    description="Small OpenAI/Anthropic library to support chat templates, and function calls",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/benderv/autochat",
)

from setuptools import setup, find_packages

setup(
    name="mydiscordbot",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "discord.py>=1.7.3",
        "transformers==4.27.4",
    ],
)

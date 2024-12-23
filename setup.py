from setuptools import setup, find_packages

setup(
    name="casys_rpg",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-socketio",
        "pydantic",
        "langchain",
        "langchain-openai",
        "openai",
        "pytest",
    ],
    python_requires=">=3.8",
)

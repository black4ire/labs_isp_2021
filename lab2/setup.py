from setuptools import setup

setup(
    name="s-tool",
    version="1.0.0",
    description="Custom serializers for TOML and JSON,"
                + " other two are based on defaults.",
    packages=["serializers"],
    python_requires=">=3.8",
    author="Masha",
    author_email="mariya.gm.4@mail.ru",
    entry_points={
        "console_scripts": [
            "convert = serializers.main:main"
            ]
        }
    )

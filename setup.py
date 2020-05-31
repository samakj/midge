from setuptools import setup

setup(
    name="midge",
    version="0.1",
    description="A small paho.mqtt wrapper",
    url="http://github.com/samakj/midge",
    author="Sam Jones",
    author_email="samakj@live.co.uk",
    license="MIT",
    package_dir={"": "."},
    packages=[
        "midge",
        "midge.handlers",
        "midge.models",
        "midge.topics",
        "midge.topics.decorators",
    ],
    install_requires=["paho-mqtt"],
    zip_safe=False
)

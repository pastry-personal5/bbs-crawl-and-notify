from setuptools import setup, find_packages

setup(
    name="bbs_crawl_and_notify",
    version="1.0.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[

    ],
    python_requires=">=3.13.1",
    author="Zhang-hoon Dennis Oh",
    description="This project retrieves content from websites and sends it to a Telegram chat room.",
    license="APACHE-2.0",
)

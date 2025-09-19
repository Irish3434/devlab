from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="picture-finder",
    version="1.0.0",
    author="Picture Finder Team",
    author_email="contact@picturefinder.com",
    description="A polished Python app for detecting duplicate images, separating videos, and managing photos",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/PictureFinder",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Graphics",
        "Topic :: System :: Archiving :: Backup",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "picture-finder=app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "assets": ["icon.ico", "locales/*.json"],
    },
)
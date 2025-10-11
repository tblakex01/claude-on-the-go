"""
Setup configuration for claude-on-the-go
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="claude-on-the-go",
    version="1.0.0",
    author="Matthew Jamison",
    author_email="99699313+MatthewJamisonJS@users.noreply.github.com",
    description="Access Claude Code CLI from your mobile device over WiFi",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MatthewJamisonJS/claude-on-the-go",
    project_urls={
        "Bug Reports": "https://github.com/MatthewJamisonJS/claude-on-the-go/issues",
        "Source": "https://github.com/MatthewJamisonJS/claude-on-the-go",
        "Documentation": "https://github.com/MatthewJamisonJS/claude-on-the-go#readme",
    },
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: User Interfaces",
        "Topic :: Terminals",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Environment :: Web Environment",
        "Framework :: FastAPI",
    ],
    keywords="claude terminal mobile websocket pwa",
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "claude-on-the-go=claude_on_the_go.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "claude_on_the_go": [
            "../legacy/**/*",
            "../core/**/*",
            "../integrations/**/*",
            "../client/**/*",
            "../scripts/**/*",
        ],
    },
    zip_safe=False,
)

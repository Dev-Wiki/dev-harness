# Windows terminal and evidence guide

[English](windows-shell.en.md) | [简体中文](windows-shell.md)

Read this guide only when a command requires a Windows host or terminal / encoding issues affect evidence assessment.

- Prefer the terminal required by the repository or toolchain. Visual Studio / MSBuild projects normally need PowerShell or cmd with the appropriate developer environment loaded.
- Treat Git Bash, MSYS2, Cygwin, and WSL as distinct execution environments. Do not start expensive native Windows builds in them until repository evidence establishes compatible path, quoting, process, and SDK behavior.
- Record the terminal, working directory, toolchain probe commands, and necessary environment initialization with the command.
- Native Windows tools may emit legacy code pages such as 936/GBK. Preserve raw bytes or record the current code page; garbled text alone does not establish a product defect.
- A terminal mismatch is a prerequisite gap, not proof that the build command itself is invalid.

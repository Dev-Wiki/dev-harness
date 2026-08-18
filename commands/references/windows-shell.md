# Windows shell and evidence guidance

Read this only for Windows-hosted commands or when terminal/encoding problems affect evidence.

- Prefer the shell required by the repository or toolchain. For Visual Studio/MSBuild projects this is commonly PowerShell or cmd with the expected developer environment loaded.
- Treat Git Bash, MSYS2, Cygwin, and WSL as distinct execution environments. Do not launch a long native Windows build there until repository evidence says the path, quoting, process, and SDK behavior is supported.
- Record the shell, working directory, toolchain discovery command, and relevant environment setup with the command record.
- Native Windows tools may emit using a legacy code page such as 936/GBK. Preserve the original bytes or record the active code page; do not interpret garbled output as a product failure.
- A terminal mismatch is a precondition gap, not proof that the build command is invalid.

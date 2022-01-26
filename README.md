# shell_emulator

A simple sh-like shell emulator, with custom filesystems, coded in python.

Originally made for a school project with more content, I decided to put the shell emulation part here because I find it relatively cool.


## How to use

To use, run the file 'main.py' using python3 in a terminal.

By default, the program will ask for login credentials, here you can use the username 'user1' with the password 'password1'.

All information about the filesystem can be found in the '.fsf' file, which defines a simulated filesystem used by the shell. The 'main.py' file is hard-coded to use the file 'default.fsf', which is included in the repo.

After successful login, the 'help' command can be used to display all available shell commands, with descriptions. The commands themselves support the '--help' launch argument, which displays more detailed information about the given command.

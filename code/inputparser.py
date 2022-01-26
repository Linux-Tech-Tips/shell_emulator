import filesystem as fs
import math as math
import colors as c

# Static class, parses user input and calls appropriate scripts

# Info for parsers of code from this class: Directives
#   - Any code starting with #DCTV: directive, makes the parser do something instead of outputting literally said line

class InputParser:

    # INFO: Not used yet: ignore for now
    # Last executed script's exit code
    LAST_EXIT_CODE = 0

    # Splits string by delimiter, while keeping quoted string together (but removing the quotes)
    @staticmethod
    def splitArgs(args, delimiter = " "):
        finalArgs = []
        quotes = False
        if len(args) > 0:
            finalArgs.append("")
            for s in args:
                # Finding whether quotes on or not
                if quotes == "\"":
                    if s == "\"":
                        quotes = False
                    else:
                        finalArgs[-1] += s
                elif quotes == "'":
                    if s == "'":
                        quotes = False
                    else:
                        finalArgs[-1] += s
                elif not quotes:
                    # Doing thing if quotes aren't, separating by ' '
                    if s == delimiter:
                        finalArgs.append("")
                    elif s == "\"" or s == "'":
                        quotes = s
                    else:
                        finalArgs[-1] += s
        return finalArgs

    # Associative array with command names as keys and lambdas calling commands as values
    COMMANDS_INDEX = {
        "cd": (lambda filesystem, args : InputParser.cd(filesystem, args)),
        "ls": (lambda filesystem, args: InputParser.ls(filesystem, args)),
        "cat": (lambda filesystem, args: InputParser.cat(filesystem, args)),
        "echo": (lambda filesystem, args: InputParser.echo(filesystem, args)),
        "touch": (lambda filesystem, args: InputParser.touch(filesystem, args)),
        "rm": (lambda filesystem, args: InputParser.rm(filesystem, args)),
        "mkdir": (lambda filesystem, args: InputParser.mkdir(filesystem, args)),
        "rmdir": (lambda filesystem, args: InputParser.rmdir(filesystem, args)),
        "dirname": (lambda filesystem, args: InputParser.dirname(filesystem, args)),
        "pwd": (lambda filesystem, args: InputParser.pwd(filesystem, args)),
        "help": (lambda filesystem, args: InputParser.showhelp(filesystem, args)),
        "exit": (lambda filesystem, args: InputParser.exit()),
        }

    @staticmethod
    def parseInput(userInput, filesystem):

        commands = userInput.strip().split(";")

        outBuffer = ""
        
        # Splitting by ;
        for splitInput in commands:
            
            outFile = False
            currentOutBuffer = ""
            # Splitting by >
            delimiter = (">>" if (">>" in splitInput) else (">" if (">" in splitInput) else False))
            if delimiter != False:
                temp = splitInput.split(delimiter, 1)
                splitInput = temp[0]
                outFile = temp[1]
            # Executing command
            splitInput = splitInput.strip()
            args = InputParser.splitArgs(splitInput)
            if len(args) < 1:
                currentOutBuffer += ""
            else:
                command = args.pop(0)
                if not (command in InputParser.COMMANDS_INDEX):
                    currentOutBuffer += "Error: unknown command: " + command + "\n"
                else:
                    result = InputParser.COMMANDS_INDEX[command](filesystem, args)
                    if type(result) is str:
                        currentOutBuffer += result
            # Saving command output into file or into stdout
            if not outFile:
                outBuffer += currentOutBuffer
            else:
                outFile = filesystem.resolvePath(outFile.strip())
                outPath = filesystem.getParent(outFile, True)
                # Creating path if doesn't exist
                if type(filesystem.getContentByPath(outPath[0], fs.DIRECTORY)) is str:
                    InputParser.mkdir(filesystem, ["-p", outPath[0]])
                # Creating file
                actualFile = filesystem.getContentByPath(outFile, fs.FILE)
                if type(actualFile) is str:
                    filesystem.createFile(outFile, True, "." + outFile.replace("/", "-"), False, True, currentOutBuffer)
                else:
                    if delimiter == ">":
                        actualFile.writeData(currentOutBuffer)
                    elif delimiter == ">>":
                        actualFile.appendData(currentOutBuffer)

        return outBuffer

    # --- SIMULATED BASH COMMANDS --- #

    @staticmethod
    def cd(filesystem, args):
        if len(args) == 1:
            path = args[0].strip()
            if path == "--help":
                LAST_EXIT_CODE = 0
                return "Usage: cd [DIRECTORY]\n  Change the shell working directory to the DIRECTORY argument, by default to the current user's home folder"
            elif path.startswith("-"):
                LAST_EXIT_CODE = 1
                return "Shell: cd: unknown option: " + path
        elif len(args) == 0:
            path = filesystem.homePath
        else:
            LAST_EXIT_CODE = 1
            return "Shell: cd: too many arguments\nUsage: cd [path]\n  change directory to given path, if no path given, change to home directory"
        if not type(filesystem.getContentByPath(path, fs.FILE)) is str:
            LAST_EXIT_CODE = 1
            return "Shell: cd: error: couldn't change directory, target " + path + " is a file\n"
        result = filesystem.changeCurrentDir(path)
        LAST_EXIT_CODE = 0
        if type(result) is str:
            LAST_EXIT_CODE = 1
            return result + "\n"

    @staticmethod
    def ls(filesystem, args):
        # parsing args
        charargs = []
        for arg in args:
            if (len(arg) > 1) and (arg[0] == "-") and (arg[1] != "-"):
                for ch in arg[1:]:
                    charargs.append(ch)
        # output style change
        showhelp = ("--help" in args)
        longlist = ("l" in charargs)
        # output modifiers
        humanreadable = ("h" in charargs or "--human-readable" in args)
        sizes = {1: "", 3: "K", 6: "M", 9: "G", 12: "T"} # Sizes for the human readable file formatting
        listall = ("a" in charargs or "--all" in args)
        listalmost = ("A" in charargs or "--almost-all" in args)
        lista = listall or listalmost # whether to hide files starting with . or not
        # file or dir to list
        target = ("./" if (len(args) < 1 or args[-1].startswith("-")) else args[-1])

        LAST_EXIT_CODE = 0

        # actually returning things
        if showhelp:
            result = "Usage: ls [OPTION]... [FILE or DIRECTORY]\n"
            result += "List information about the FILE or DIRECTORY (current directory by default)\n"
            result += "Listed entries are sorted alphabetically\n"
            result += "\narguments:\n"
            result += "  -a, --all              don't hide files starting with .\n"
            result += "  -A, --almost-all       don't hide files starting with . except for implied . (current dir) and .. (parent dir)\n"
            result += "  -h, --human-readable   show file sizes in human readable format\n"
            result += "  --help                 display this help info\n"
            result += "  -l                     use a long listing format"
            return result + "\n"
            # return help
        else:
            names = []
            if listall:
                if longlist:
                    names.append("drwxr-xr-x " + filesystem.defaultUser + (" 4.0K" if humanreadable else " 4096") + " .")
                    names.append("drwxr-xr-x " + filesystem.defaultUser + (" 4.0K" if humanreadable else " 4096") + " ..")
                else:
                    names.append(c.BLUE_BOLD + "." + c.NO_COLOR)
                    names.append(c.BLUE_BOLD + ".." + c.NO_COLOR)
            # getting to target dir
            lastDir = filesystem.currentDir.getPath()
            changeResult = filesystem.changeCurrentDir(target, True)
            result = ""
            
            if type(changeResult) is str:
                # Target is not a directory, could be a file, find if file and list file info
                splitTarget = filesystem.getParent(target, True)
                parent = splitTarget[0]
                filename = splitTarget[1]
                # Testing whether target is an existing file, if so listing it
                changeResult = filesystem.changeCurrentDir(parent, True)
                if type(changeResult) is str:
                    LAST_EXIT_CODE = 1
                    result = changeResult
                else:
                    listedFile = filesystem.currentDir.getFile(filename)
                    if type(listedFile) is str:
                        LAST_EXIT_CODE = 1
                        result = "Error: target not found: " + target
                    else:
                        if longlist:
                            # long list of current file
                            rawfilesize = len(listedFile.ramData)
                            multiplier = max(1, (math.floor(len(str(rawfilesize)) / 3) * 3))
                            filesize = str(((str(rawfilesize / multiplier) + sizes[multiplier]) if humanreadable else rawfilesize))
                            user = (filesystem.defaultUser if listedFile.access else "root")
                            spaces = max(1, 5 - len(filesize))
                            result = ("-rwxrw-rw- " if listedFile.access else "-rwxrw---- ") + user + (" "*spaces) + filesize + " " + listedFile.name
                        else:
                            result = listedFile.name
            else:
                # Target is a directory, list content
                dirs = filesystem.currentDir.getDirs()
                files = filesystem.currentDir.getFiles()
                for d in dirs:
                    if longlist:
                        # Long list of dirs
                        names.append(("drwxrw-rw- " if d.access else "drwxrw---- ") + (filesystem.defaultUser if d.access else "root") + (" 4.0K " if humanreadable else " 4096 ") + d.name)
                    elif (not d.name.startswith(".")) or lista:
                        # Short list of dirs
                        names.append(c.BLUE_BOLD + d.name + c.NO_COLOR)
                for f in files:
                    if longlist and ((not f.name.startswith(".")) or lista):
                        # Long list of files
                        rawfilesize = len(f.ramData)
                        multiplier = max(1, (math.floor(len(str(rawfilesize)) / 3) * 3))
                        filesize = str(((str(rawfilesize / multiplier) + sizes[multiplier]) if humanreadable else rawfilesize))
                        user = (filesystem.defaultUser if f.access else "root")
                        spaces = max(1, 5 - len(filesize)) + max(0, len(filesystem.defaultUser) - len(user))
                        names.append(("-rwxrw-rw- " if f.access else "-rwxrw---- ") + user + (" "*spaces) + filesize + " " + f.name)
                    elif (not f.name.startswith(".")) or lista:
                        # Short list of files
                        names.append(f.name)
                # Adding all to result
                for n in names:
                    result += n + (("\n" if longlist else " ") if (names.index(n) < len(names) - 1) else "")
            filesystem.changeCurrentDir(lastDir, True)
            return result + "\n"

    @staticmethod
    def cat(filesystem, args):
        LAST_EXIT_CODE = 0
        if len(args) > 0:
            params = []
            for a in args:
                if (len(a) > 1 and (a[0] == "-" and a[1] != "-")):
                    for i in a[1:]:
                        params.append(i)
                elif a.startswith("--"):
                    params.append(a[2:])
            
            # return help
            if "help" in params:
                result = "Usage: cat [OPTIONS] <FILE>\n"
                result += "Concatenate FILE content to standard output\n\n"
                result += "Arguments:\n"
                result += "  -n, --number      number all output lines\n"
                result += "  -E, --show-ends   display $ at end of each line\n"
                result += "  --help            display this help info"
                return result + "\n"
    
            number = ("n" in params or "number" in params)
            lineends = ("E" in params or "show-ends" in params)

            if not args[-1].startswith("-"):
                reqpath = args[-1]
                file = filesystem.getContentByPath(reqpath, fs.FILE)
                if type(file) is str:
                    LAST_EXIT_CODE = 1
                    return "Error: cat: file " + reqpath + " not found\n"
                else:
                    data = file.getData()
                    result = ""
                    num = 0
                    for line in data.split("\n"):
                        result += ((str(num) + "  ") if number else "") + line + ("$" if lineends else "") + "\n"
                        num += 1
                    return result
            else:
                LAST_EXIT_CODE = 1
                return "Error: cat: missing file argument\n"
        else:
            LAST_EXIT_CODE = 1
            return "Error: cat: missing file argumen\nt"

    @staticmethod
    def echo(filesystem, args):
        LAST_EXIT_CODE = 0
        end = "\n"
        if "-n" in args:
            end = ""
            args.remove("-n")
        result = ""
        for a in args:
            result += a + " "
        return result + end

    @staticmethod
    def touch(filesystem, args):
        LAST_EXIT_CODE = 0
        if "--help" in args:
            result = "Usage: touch FILE...\n"
            result += "Creates specified FILE(s)\n"
            return result
        
        # Creating specified files
        if len(args) > 0:
            for a in args:
                path = filesystem.resolvePath(a.strip())
                createResult = filesystem.createFile(path, True, "." + path.replace("/", "-"), False, True, "")
                if type(createResult) is str:
                    LAST_EXIT_CODE = 1
                    return "Error: touch: " + createResult + "\n"
        else:
            LAST_EXIT_CODE = 1
            return "touch: missing argument\nTry 'touch --help' for more information\n"
    
    @staticmethod
    def rm(filesystem, args):
        LAST_EXIT_CODE = 0
        if len(args) > 0:
            # Parsing args
            params = []
            targets = []
            for a in args:
                if (len(a) > 1 and (a[0] == "-" and a[1] != "-")):
                    for i in a[1:]:
                        params.append(i)
                elif a.startswith("--"):
                    params.append(a[2:])
                else:
                    targets.append(a)
            
            # Doing things according to args
            # Print help
            if "help" in params:
                result = "Usage: rm [OPTION]... [FILE or DIRECTORY]...\n"
                result += "Remove the FILE(s) or DIRECTORY(s).\n\n"
                result += "  -f, --force           force remove - ignore errors, non-existent files\n"
                result += "  -r, -R, --recursive   remove directories and their content recursively\n"
                result += "  -v, --verbose         explains what is being done\n"
                result += "      --help            display this help and exit\n"
                return result
            # Actually delete
            force = ("f" in params or "force" in params)
            rec = ("r" in params or "R" in params or "recursive" in params)
            verbose = ("v" in params or "verbose" in params)
            # Finding files to delete
            result = ""
            for t in targets:
                targetpath = filesystem.resolvePath(t.strip())
                target = filesystem.getContentByPath(targetpath)
                if type(target) is str:
                    result += ("" if force else ("error: target " + t + "not found\n"))
                else:
                    parent = filesystem.getParent(targetpath, True)
                    lastDir = filesystem.getCurrentPath()
                    filesystem.changeCurrentDir(parent[0], True)
                    if target.contentType == fs.FILE:
                        filesystem.getCurrentDir().getFiles().remove(target)
                        result += (("rm: file " + t + " removed\n") if verbose else "")
                    elif target.contentType == fs.DIRECTORY:
                        if len(target.getContent()) == 0 or rec:
                            filesystem.getCurrentDir().getDirs().remove(target)
                            result += (("rm: directory " + t + " removed\n") if verbose else "")
                        else:
                            result += ("" if force else ("rm: error: couldn't remove directory " + t + ": not empty\n"))
                    filesystem.changeCurrentDir(lastDir, True)
            return result
        else:
            return "rm: missing argument\nTry 'rm --help' for more information\n"
    
    @staticmethod
    def mkdir(filesystem, args):
        if len(args) > 0:
            LAST_EXIT_CODE = 0
            # Passing arguments
            params = []
            for a in args:
                if (len(a) > 1 and (a[0] == "-" and a[1] != "-")):
                    for i in a[1:]:
                        params.append(i)
                elif a.startswith("--"):
                    params.append(a[2:])
                    
            if "help" in params:
                result = "Usage: mkdir [OPTION]... DIRECTORY\n"
                result += "Create the DIRECTORY if it doesn't exist\n\n"
                result += "Arguments:\n"
                result += "  -p, --parents    make parent directories as well if needed\n"
                result += "  -v, --verbose    print a message for each created directory"
                return result + "\n"
            
            parents = ("p" in params or "parents" in params)
            verbose = ("v" in params or "verbose" in params)
            path = filesystem.resolvePath(args[-1])
            # Finding whether path exists
            searchResult = filesystem.getContentByPath(path)
            if not type(searchResult) is str:
                LAST_EXIT_CODE = 1
                return "mkdir: error: target '" + path + "' already exists\n"
            # Creating directory
            if parents:
                result = ""
                current = "/"
                for part in path.strip(" /").split("/"):
                    current += part + "/"
                    searchResult = filesystem.getContentByPath(current)
                    if type(searchResult) is str:
                        # Creating parent folder
                        createResult = filesystem.createFolder(current, True)
                        if type(createResult) is str:
                            LAST_EXIT_CODE = 1
                            return "mkdir: error creating folders: " + createResult + "\n"
                        result += (("mkdir: created directory '" + current + "'\n") if verbose else "")
                return result
            else:
                createResult = filesystem.createFolder(path, True)
                if type(createResult) is str:
                    return createResult + "\n"
                else:
                    return (("mkdir: created directory '" + path + "'\n") if verbose else "")
        else:
            LAST_EXIT_CODE = 1
            return "mkdir: missing argument\nTry 'mkdir --help' for more information\n"
    
    @staticmethod
    def rmdir(filesystem, args):
        if len(args) > 0:
            LAST_EXIT_CODE = 0
            # Passing arguments
            params = []
            for a in args:
                if (len(a) > 1 and (a[0] == "-" and a[1] != "-")):
                    for i in a[1:]:
                        params.append(i)
                elif a.startswith("--"):
                    params.append(a[2:])
                    
            if "help" in params:
                result = "Usage: rmdir [OPTION]... DIRECTORY\n"
                result += "Remove the DIRECTORY if it is empty\n\n"
                result += "Arguments:\n"
                result += "  -p, --parents    remove a directory with all of its ancestors: 'rmdir -p a/b/c' removes a, b and c; 'rmdir a/b/c' removes only c\n"
                result += "  -v, --verbose    print a message for each removed directory"
                return result + "\n"
            
            parents = ("p" in params or "parents" in params)
            verbose = ("v" in params or "verbose" in params)
            path = args[-1]
            # Finding whether path exists - can't remove if doesn't exist
            searchResult = filesystem.getContentByPath(path)
            if type(searchResult) is str:
                LAST_EXIT_CODE = 1
                return "rmdir: error: target '" + path + "' doesn't exist\n"
            
            # Removing dir
            if parents:
                # Remove parent dirs as well
                result = ""
                lastDir = filesystem.getCurrentPath()
                currentPath = path
                target = ""
                while True:
                    filesystem.changeCurrentDir(lastDir, True)
                    parts = filesystem.getParent(currentPath, True)
                    currentPath = parts[0]
                    target = parts[1]
                    # Exit loop if the current target is . meaning the whole requested path has been gone through
                    if target == "." or target == "":
                        break
                    # Test whether current path can be changed to
                    changeResult = filesystem.changeCurrentDir(currentPath, True)
                    if type(changeResult) is str:
                        result += "rmdir: error: can't find parent dir '" + currentPath + "'\n"
                        LAST_EXIT_CODE = 1
                        break
                    # Test whether current target exists
                    targetDir = filesystem.getCurrentDir().getDir(target)
                    if type(targetDir) is str:
                        result += "rmdir: error: can't find dir to remove '" + target + "'\n"
                        LAST_EXIT_CODE = 1
                        break
                    # Test whether current target is empty
                    if len(targetDir.getContent()) > 0:
                        result += "rmdir: error: dir '" + target + "' not empty\n"
                        LAST_EXIT_CODE = 1
                        break
                    # Test whether access to dir
                    if targetDir.access:
                        # Removing dir
                        filesystem.getCurrentDir().getDirs().remove(targetDir)
                        result += (("rmdir: removed directory '" + currentPath + "/" + target + "'\n") if verbose else "")
                    else:
                        result += "rmdir: error: access to dir '" + currentPath + "/" + target + "' forbidden\n"
                        LAST_EXIT_CODE = 1
                        break
                filesystem.changeCurrentDir(lastDir, True)
                return result
            
            else:
                # Remove only selected dir
                result = ""
                lastDir = filesystem.getCurrentPath()
                parent = filesystem.getParent(path, True)
                filesystem.changeCurrentDir(parent[0])
                currentDir = filesystem.getCurrentDir()
                if len(currentDir.getDir(parent[1]).getContent()) == 0:
                    if currentDir.getDir(parent[1]).access:
                        currentDir.getDirs().remove(currentDir.getDir(parent[1]))
                        result = (("rmdir: removed directory '" + path + "'\n") if verbose else "")
                    else:
                        result = "rmdir: error: access to dir '" + path + "' forbidden\n"
                        LAST_EXIT_CODE = 1
                else:
                    result = "rmdir: error: couldn't remove dir '" + path + "', dir isn't empty\n"
                    LAST_EXIT_CODE = 1
                filesystem.changeCurrentDir(lastDir, True)
                return result

        else:
            LAST_EXIT_CODE = 1
            return "rmdir: missing argument\nTry 'rmdir --help' for more information\n"

    @staticmethod
    def dirname(filesystem, args):
        LAST_EXIT_CODE = 0
        if "--help" in args:
            result = "Usage: dirname NAME...\n"
            result += "Output each NAME with its last non-slash component and trailing slashes removed, if name contains no slashes, . gets returned"
            return result + "\n"
        result = ""
        if len(args) < 1:
            result = "dirname: missing argument\nTry 'dirname --help' for more information"
            LAST_EXIT_CODE = 1
        for a in args:
            result += filesystem.getParent(a) + " "
        return result + "\n"

    @staticmethod
    def pwd(filesystem, args):
        LAST_EXIT_CODE = 0
        if ("--help" in args) or (len(args) > 0):
            return "usage: pwd\n  Print the name of the current working directory\n"
        else:
            return filesystem.getCurrentPath() + "\n"

    @staticmethod
    def showhelp(filesystem, args):
        result = "Python Simulated Shell (PSH) - Version 1.0 Help\n"
        result += "Displaying help information about the simulated shell\n\n"
        result += "Available commands:\n"
        result += " echo [-n] [TEXT] ............................ Prints the given text to standard output (optionally specify -n to exclude printing closing line break)\n"
        result += " cd [DIRECTORY] .............................. Change current directory to the given DIRECTORY argument\n"
        result += " ls [OPTION(s)] [FILE or DIRECTORY] .......... Lists contents of the specified directory or information about the specified file (see ls --help for more info)\n"
        result += " cat [OPTION(s)] <FILE> ...................... Prints contents of specified FILE to standard output (see cat --help for more info)\n"
        result += " mkdir [OPTION(s)] DIRECTORY ................. Creates a directory with the specified name/path (see mkdir --help for more info)\n"
        result += " rmdir [OPTION(s)] DIRECTORY ................. Removes the directory on the specified path (see rmdir --help for more info)\n"
        result += " touch FILE(s) ............................... Creates the specified file(s)\n"
        result += " rm [OPTION(s)] [FILE or DIRECTORY] .......... Removes the specified FILE or DIRECTORY (see rm --help for more info)\n"
        result += " dirname NAME ................................ Outputs the parent directory of the specified NAME, returns . if it's the current directory\n"
        result += " pwd ......................................... Prints current working directory\n"
        result += " help ........................................ Displays this help\n"
        result += " exit ........................................ Quits the shell\n\n"
        result += "Available output redirection info:\n"
        result += " Standard output from commands (like 'echo') can be redirected into a file using the '>' operator\n"
        result += " Standard output from commands can be appended to a file using the '>>' operator\n"
        result += " Syntax: \n"
        result += "  COMMAND > FILE to overwrite content of FILE with COMMAND output\n"
        result += "  COMMAND >> FILE to append content of FILE with COMMAND output\n"
        return result

    @staticmethod
    def exit():
        return "#DCTV exit"


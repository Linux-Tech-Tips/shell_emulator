import filesystem as fs

# Script to parse FSF files into a Linux-like custom filesystem

class FilesystemParser:

    # Returns either Filesystem instance or str if failed
    @staticmethod
    def loadFSF(fileData):

        # Variables that need to be set
        hostname = "host"
        defaultAllowed = True
        defaultUser = "user"
        homePath = "/home/"
        users = {}

        # Getting lines
        lines = (fileData.split("\n") if type(fileData) is str else fileData)

        if lines.pop(0) != "#FSF":
            return "Failed parsing file: format not correct"
        # Parsing lines
        sections = {}
        currentName = "none"
        sections[currentName] = []

        for line in lines:
            # Removing comments
            sLine = line.split("#", 1)[0]
            if len(sLine) < 1:
                continue
            if (sLine[0] == "[" and sLine[-1] == "]"):
                currentName = sLine.strip(" []")
                sections[currentName] = []
            else:
                sections[currentName].append(sLine.strip())

        # Getting data from sections
        if ("info" in sections) and ("users" in sections) and ("fs" in sections):
            # Info
            infoSection = sections["info"]
            for i in infoSection:
                pair = i.split("=", 1)
                if pair[0] == "hostname":
                    hostname = pair[1]
                elif pair[0] == "defaultallowed":
                    defaultAllowed = (True if pair[1] == "true" else False)
                elif pair[0] == "defaultuser":
                    defaultUser = pair[1]
                elif pair[0] == "homepath":
                    homePath = pair[1]
            # Users
            userSection = sections["users"]
            for u in userSection:
                pair = u.split("=", 1)
                users[pair[0]] = pair[1]
        else:
            return "Failed parsing file: missing sections"

        # Creating Filesystem instance, parsing data from fs section
        result = fs.Filesystem(users, defaultAllowed, defaultUser, homePath, hostname)
        fsSection = sections["fs"]
        for entry in fsSection:
            if (len(entry) < 0) or (not (";" in entry)):
                continue
            # Getting info about entry
            parts = entry.split(";")
            parent = parts[0]
            name = parts[1]
            entryType = parts[2]
            access = parts[3]
            # Getting to correct parent path
            if not (result.getCurrentPath() == parent):
                result.changeCurrentDir(parent, True)
            # Adding entry
            if entryType == "d":
                result.getCurrentDir().addDirectory(fs.Directory(parent + name + "/", (True if access == "true" else False)))
            elif entryType == "f":
                realPath = parts[4]
                loadRealData = parts[5]
                result.getCurrentDir().addFile(fs.File(parent + name + "/", (True if access == "true" else False), realPath, (True if loadRealData == "true" else False), (True if loadRealData == "true" else False)))
        # Resetting the result to default after adding directories
        result.changeCurrentDir(result.homePath, True)
        return result

    # Inner method used by the FilesystemParser
    @staticmethod
    def writeDirContent(directory, realWriteFiles = True):

        strBuffer = ""
        # Writing directories with their subdirs
        subdirs = directory.getDirs()
        if len(subdirs) > 0:
            for d in subdirs:
                # Writing directory into file
                parts = d.path.rstrip("/").split("/")
                name = parts.pop()
                parent = "/".join(parts) + "/"
                strBuffer += (parent + ";" + name + ";d;" + ("true" if d.access else "false") + "\n")
                # Recursively writing subfolders
                if len(d.getDirs()) > 0 or len(d.getFiles()) > 0:
                    strBuffer += FilesystemParser.writeDirContent(d, realWriteFiles)

        # Writing files
        files = directory.getFiles()
        if len(files) > 0:
            for f in files:
                # Writing file info into output buffer
                parts = f.path.rstrip("/").split("/")
                name = parts.pop()
                parent = "/".join(parts) + "/"
                strBuffer += (parent + ";" + name + ";f;" + ("true" if f.access else "false") + ";" + f.realPath + ";" + ("true" if f.useRealData else "false") + "\n")
                # Saving actual file if realWriteFiles
                if realWriteFiles:
                    f.realWriteData()

        return strBuffer

    # Returns str to write into file
    @staticmethod
    def saveFSF(filesystem, realWriteFiles = True):

        # Variables
        fileBuffer = "#FSF\n\n"

        # Writing info section
        fileBuffer += "[info]\n\n"

        fileBuffer += "hostname=" + str(filesystem.host) + "\n"
        fileBuffer += "defaultallowed=" + ("true" if filesystem.defaultAllowed else "false") + "\n"
        fileBuffer += "defaultuser=" + str(filesystem.defaultUser) + "\n"
        fileBuffer += "homepath=" + str(filesystem.homePath) + "\n"
        fileBuffer += "\n"

        # Writing users section
        fileBuffer += "[users]\n\n"

        for u in filesystem.users:
            name = u
            passwd = filesystem.users[name]
            fileBuffer += str(name) + "=" + str(passwd) + "\n"
        fileBuffer += "\n"

        # Writing fs section
        fileBuffer += "[fs]\n\n"
        fileBuffer += FilesystemParser.writeDirContent(filesystem.rootDir, realWriteFiles)

        return fileBuffer

# Filesystem file: contains classes that define a Linux-like custom filesystem in python memory for easy access

DIRECTORY = 0
FILE = 1
ALL_TYPES = 2

class Filesystem:
    
    # --- BASIC THINGS ---
    
    def __init__(self, users, defaultAllowed = True, defaultUser = "user", homePath = "/home/", hostname = "linuxdevice"):
        # Filesystem file data info
        self.rootDir = Directory("/", True)
        self.currentDir = self.rootDir
        self.homePath = homePath
        # Filesystem user info
        self.users = users
        self.defaultUser = defaultUser
        self.defaultAllowed = defaultAllowed
        self.user = (defaultUser if defaultAllowed else None)
        self.host = hostname
        # Login management
        self.login = defaultAllowed
    
    def logIn(self, username, password):
        if ((username in self.users) and (self.users[username] == password)):
            self.user = username
            self.login = True
            return "Logged in successfully\n\nWelcome to Python Simulated Shell (PSH) - Version 1.0\nType 'help' to show shell capabilities"
        else:
            self.login = False
            return "Error: Incorrect credentials"
    
    # --- GET METHODS ---
    
    def getCurrentDir(self):
        return self.currentDir
    def getCurrentPath(self):
        return self.currentDir.getPath()
    
    # Returns the directory on the path relative to given root
    def findDir(self, rootDir, path):
        # Returning the root dir if requested path is root
        if path == "/":
            return rootDir
        # Searching for a given path if more than root
        parts = path.strip("/").split("/")
        tmpDir = rootDir
        
        for part in parts:
            changed = False
            for subdir in tmpDir.getDirs():
                if subdir.name == part:
                    tmpDir = subdir
                    changed = True
            if (not changed):
                return "Error: directory not found: " + str(path)
        return tmpDir
    
    # Returns pointer to the given content if it exists, if not, str with error message is returned
    def getContentByPath(self, path, contentType = ALL_TYPES):
        absPath = self.resolvePath(path.strip())
        result = self.findDir(self.rootDir, absPath)
        if (not (type(result) is str)) and (contentType != FILE):
            return result
        elif contentType != DIRECTORY:
            parent = self.getParent(absPath, True)
            directory = self.findDir(self.rootDir, parent[0])
            if type(directory) is str:
                return "Error: couldn't get content: directory not found"
            else:
                result = directory.getFile(parent[1].strip(" /"))
                if type(result) is str:
                    return "Error: couldn't get content: file not found"
                else:
                    return result
        else:
            return "Error: couldn't get content"
            
    # Convenience method, finds the parent directory name of the given path
    def getParent(self, path, includeCurrent = False):
        path = path.strip()
        parent = "."
        current = "."
        if len(path) > 0:
            absolute = path.startswith("/")
            endSlash = path.endswith("/")
            parts = path.strip("/ ").split("/")
            current = parts.pop()
            parent = (("/" if absolute else ".") if (len(parts) < 1) else ("/" if absolute else "") + "/".join(parts) + ("/" if endSlash else ""))

        if includeCurrent:
            return [parent, current]
        else:
            return parent 
    
    # Convenience method, resolves any path to be absolute (begin with /, relative to the fs root dir)
    def resolvePath(self, path):
        # Changing relative path to absolute
        if path[-1] != "/":
            path += "/"
        if path.startswith("/"):
            abspath = path
        elif path.startswith("./"):
            abspath = self.getCurrentPath() + path[2:]
        else:
            abspath = self.getCurrentPath() + path
        # Removing ../ - changing into just listing the parent directory instead
        abspath = abspath.split("/")
        shift = 0 # how many elements were removed - how much should the indexes when checking the list shift
        for i in range(len(abspath)):
            j = i - shift
            if abspath[j] == "..":
                if j > 1:
                    abspath.pop(j)
                    abspath.pop(j-1)
                    shift += 2
                else:
                    return "Error: could not resolve path"
        abspath = "/".join(abspath)
        return abspath
    
    # --- CHANGE METHODS ---
    
    # Changes Filesystem currentDir to the directory specified by the path, supports relative paths + ../
    def changeCurrentDir(self, path, noAuth = False):
        if self.login or noAuth:
            if len(path) > 0:
                abspath = self.resolvePath(path.strip())
                # Changing the current directory to the one specified by the path
                result = self.findDir(self.rootDir, abspath)
                if type(result) is str:
                    return result
                else:
                    if result.access:
                        self.currentDir = result
                    else:
                        return "Error: access to directory " + abspath + " forbidden"
            else:
                return "Error: invalid path " + path
        else:
            return "Error: must be logged in to change directory"
    
    # Creates a folder with the given params
    def createFolder(self, path, access):
        lastDir = self.getCurrentPath()
        absPath = self.resolvePath(path.strip())
        changeResult = self.changeCurrentDir(self.getParent(absPath))
        if type(changeResult) is str:
            return changeResult
        if type(self.getContentByPath(absPath)) is str:
            self.getCurrentDir().addDirectory(Directory(absPath, access))
        else:
            return "Error: can't create folder: content " + absPath + " already exists"
        self.changeCurrentDir(lastDir, True)
    
    # Creates a file with the given params
    def createFile(self, path, access, realPath, loadRealData, saveRealData, ramData):
        lastDir = self.getCurrentPath()
        absPath = self.resolvePath(path.strip())
        changeResult = self.changeCurrentDir(self.getParent(absPath))
        if type(changeResult) is str:
            return changeResult
        if type(self.getContentByPath(absPath)) is str:
            self.getCurrentDir().addFile(File(absPath, access, realPath, loadRealData, saveRealData))
            self.getCurrentDir().getFile(self.getParent(absPath, True)[1]).writeData(ramData)
        else:
            return "Error: can't create file: content " + absPath + " already exists"
        self.changeCurrentDir(lastDir, True)
    
class Directory:
    
    def __init__(self, path, access):
        self.contentType = DIRECTORY
        self.path = path
        self.name = ("root" if path == "/" else path.strip("/ ").split("/")[-1])
        self.access = access
        self.dirs = []
        self.files = []
    
    def getPath(self):
        return self.path
    def getName(self):
        return self.name
    
    def getContent(self):
        return self.dirs + self.files
    def getDirs(self):
        return self.dirs
    def getDir(self, dirname):
        for d in self.dirs:
            if d.name == dirname:
                return d
        return "Error: directory " + dirname + " not found"
    def getFiles(self):
        return self.files
    def getFile(self, filename):
        for f in self.files:
            if f.name == filename:
                return f
        return "Error: file " + filename + " not found"
    
    def addDirectory(self, childDir):
        self.dirs.append(childDir)
    def addFile(self, childFile):
        self.files.append(childFile)

class File:
    
    def __init__(self, path, access, realPath, loadRealData, saveRealData):
        self.contentType = FILE
        # Filesystem things
        self.path = path
        self.name = path.strip("/ ").split("/")[-1]
        self.access = access
        # File data things
        self.changed = False
        self.realPath = realPath
        self.ramData = ""
        self.useRealData = saveRealData
        if loadRealData:
            try:
                f = open(realPath, "r")
                self.ramData = f.read()
                f.close()
            except:
                pass
    
    def getPath(self):
        return self.path
    def getName(self):
        return self.name
    
    def realWriteData(self):
        if self.changed and self.useRealData:
            f = open(self.realPath, "w+")
            f.write(self.ramData)
            f.close()
    
    def getData(self):
        return self.ramData
    def appendData(self, data):
        self.ramData += data
        self.changed = True
    def writeData(self, data):
        self.ramData = data
        self.changed = True
    

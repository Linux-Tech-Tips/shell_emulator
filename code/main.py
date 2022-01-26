from filesystem import *
from inputparser import *
from fsfparser import *
from getpass import *
import colors as c
import sys

# Main script, allows using the actual filesystem classes from a terminal to emulate a shell

# INFO:
# The command 'help' will tell you information about the capabilities of this simulated shell

args = sys.argv

if len(args) > 1:
    if args[1] == "no_color":
        c.disableColor()

fsfName = "default.fsf"

f = open(fsfName, "r")
fData = f.read()
f.close()
testFS = FilesystemParser.loadFSF(fData)

try:
    while True:
        
        try:
            if (not testFS.login):
                name = input("username: ")
                passw = getpass("password: ")
                print(testFS.logIn(name, passw))
            else:

                command = input(c.GREEN_BOLD + testFS.user + "@" + testFS.host + c.WHITE_BOLD + ":" + c.BLUE_BOLD + testFS.getCurrentDir().path.replace(testFS.homePath, "~/") + "$ " + c.NO_COLOR)

                result = InputParser.parseInput(command, testFS)
                if type(result) is str and len(result) > 0:
                    if result.startswith("#DCTV"):
                        directive = result.split(" ", 1)[1]
                        if directive == "exit":
                            break
                    else:
                        print(result, end = "")
        except KeyboardInterrupt:
            print("")
except EOFError:
    print("")
except Exception as e:
    print("Encountered unexpected error, exiting program")
    print("Error: " + str(e))

f = open(fsfName, "w+")
fsSave = FilesystemParser.saveFSF(testFS)
f.write(fsSave)
f.close()

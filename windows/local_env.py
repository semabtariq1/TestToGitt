import platform
import os


projectName = 'test'

vsCommandPromptX64    = "C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC"
shareLib                 = "C:\\build-python-dev\\PGInstaller\\windows\\winShareLib"
windowsCmd              = 'C:\\Windows\\system32\\cmd.exe'
signingPasswordRoot = 'C:\\semabHome\\automation\\codesign\\signing'
bitrockInstallation = 'C:\\bitrock_installation'

""" Some general variables should not be modified in any case """
root = os.path.dirname(os.path.abspath(__file__))

version = "v0.1"

print(f"""                      __
.--.--.--.---.-.-----|  |_.-----.
|  |  |  |  _  |__ --|   _|  -__|
|________|___._|_____|____|_____|{version}
""")

import os
import chevron      # mustache template
import mistletoe    # markdown renderer
import shutil       # for copying static files

# Utility functions
def env(v,default=""):
    return default if not v in os.environ else os.environ(v)

# Set up configuration vars 
SOURCE_PATH = env("SOURCE_PATH","/src")
OUTPUT_PATH = env("OUTPUT_PATH","/build")
STATIC_FILES = env("STATIC_FILES","/static")
TEMPLATE_PATH = env("TEMPLATE_PATH","/templates")

# load all moustache templates
print("▶️  Loading templates")
templates = {}
for root, dirs, filenames in os.walk(TEMPLATE_PATH):
    for filename in filenames:
        full_path = os.path.join(root, filename)
        fn,ex = os.path.splitext(filename)
        print('\t', full_path)
        templates[fn] = open(full_path, "r").read()

# copy static files into public directory
print("📄 Copying static files")
def copy_tree_verbose(path, names):
    print("\t", path, names)
    return []
shutil.copytree(STATIC_FILES, OUTPUT_PATH, dirs_exist_ok=True, ignore=copy_tree_verbose) #py8 required

# pre-process all markdown files

# render all files
print("🚀 Rendering markdown files into output")
for root, dirs, filenames in os.walk(SOURCE_PATH):
    for filename in filenames:
        fn,ex = os.path.splitext(filename)
        fullpath = os.path.join(root, filename)
        #print("\t",root, fn, ex, fullpath)

        obj = {}

        with open(fullpath, "r") as md:
            # update markdown if requireed before rendering

            # update mustache object
            obj["md"] = mistletoe.markdown(md)
            obj["template"] = "default"

            # load the template
            template = templates[obj["template"]]

            # render the html
            html = chevron.render(template, obj)

            # test output
            print("\t", fullpath)
            #print(html)

print("ALL DONE. BYE BYE")

version = "v0.1"

print(f"""                      __
.--.--.--.---.-.-----|  |_.-----.
|  |  |  |  _  |__ --|   _|  -__|
|________|___._|_____|____|_____|{version}
""")

import os
import chevron      # mustache template
import mistune      # markdown
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
    for f in names:
        print("\t", f )
    return []
shutil.copytree(STATIC_FILES, OUTPUT_PATH, dirs_exist_ok=True, ignore=copy_tree_verbose) #py8 required

# pre-process all markdown files

# render all files
print("🚀 Rendering markdown files into output")
for root, dirs, filenames in os.walk(SOURCE_PATH):
    for filename in filenames:
        fn,ex = os.path.splitext(filename)
        fullpath = os.path.join(root, filename)

        obj = {}
        content = ""

        # basic metadata
        obj["src_path"] = fullpath
        obj["mod_date"] = os.path.getmtime(fullpath)

        src_file = open(fullpath, "r")
        state = "metadata"
        for line in src_file:
            # read  metadata
            if state == "metadata":
                if line.startswith("---"):
                    state = "content"
                else:
                    if ":" not in line:
                        print("Error parsing metadata line (",line,") in ", fullpath)
                        continue
                    else:
                        name, value = line.strip().split(":",1)
                        name = name.strip()
                        value = value.strip()
                        if name == "tags":
                            value = value.split(",")
                        obj[name] = value
            else:
                content += line

        # update markdown if requireed before rendering
        # update mustache object
        obj["md"] = content
        obj["template"] = "default" if "template" not in obj else obj["template"]

        # load the template
        template = templates[obj["template"]]

        # render the html
        html = chevron.render(template, obj)

        # create the output file
        # /src/foo/bah.md -> /dest/foo/bah/index.md
        # $filename -> /dest/$filename
        dest_dir =  os.path.join(root, fn)
        dest_dir = os.path.join(dest_dir, 'index.html')
        dest_dir = dest_dir.replace(SOURCE_PATH,OUTPUT_PATH,1)
        dest_dir = os.path.join(OUTPUT_PATH, obj["filename"]) if "filename" in obj else dest_dir
        os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
        with open(dest_dir, "w") as dest_file:
            dest_file.write(html)

        print("\t",fullpath,"->", dest_dir)

print("ALL DONE. BYE BYE")

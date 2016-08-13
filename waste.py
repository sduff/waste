#!/usr/bin/env python 
# What, Another Site Templating Engine? WASTE
# Simon Duff <simon.duff@gmail.com>
# v0.5

# Usual Imports
import os, os.path, re, glob, sys, time, shutil, datetime, json, logging
from string import Template
# Markdown
import mistune
# Pygments
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

# Extra Mistune Config
class Renderer(mistune.Renderer):
    def block_code(self, code, lang):
        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % mistune.escape(code)
        lexer = get_lexer_by_name(lang, stripall=True)
        formatter = HtmlFormatter()
        return highlight(code, lexer, formatter)

    def link(self, link, title, text):
        # Check if link looks like a wiki-link or a real link (does it contain a .)
        if "." in link or ":" in link:
            return '<a href=\"%s\" class="ext_link" target="_blank">%s</a>'%(link, text)

        # is there an internal page that goes by this name
        print("I think the current page is ",current_page)
        if link in page :
            page[current_page]["metadata"]["reverse_links"][link] = text
            if "url" in page[link]["metadata"]:
                return '<a href=\"%s\" class="int_link">%s</a>'%(page[link]["metadata"]["url"], text)
            else:
                # use default link
                url = "/%s/"%link
                return '<a href=\"%s\" class="int_link">%s</a>'%(url, text)

        raise Exception("Dodgy Link '%s'"%link)

    def autolink(self, link, is_email=False):
        if is_email:
            return '<a href="mailto:%s" class="mail_link">%s</a>'%(link,link)
        else:
            return '<a href=\"%s\" class="ext_link" target="_blank">%s</a>'%(link, link)


md = mistune.Markdown(renderer=Renderer())

# Configre Logging
logging.basicConfig(level=logging.INFO)

# Read Config
try:
    cfg = json.load(open("waste.json"))
    template_dir = cfg["templates"]
    src = cfg["src"]
    out = cfg["out"]
    domain = cfg["domain"]
except Exception as e:
    logging.fatal(e)
    sys.exit(1)

logging.debug("Config: %s"%cfg)

# Read all files in the source directory
sf = glob.glob(os.path.join(src, "*.md"))
logging.debug("Source Files: %s", sf)

# Read all templates
templates = {}
for t in glob.glob(os.path.join(template_dir,"*")):
    tt = open(t).read()
    templates[os.path.basename(t)] = Template(tt)

# read the comment fragment
comment_html = templates["comments"]

page = {}
for f in sf:
    logging.debug("Reading File: %s", f)
    metadata = {}
    metadata["mod_time"] = os.stat(f).st_mtime
    data = open(f)
    state = 0
    text = ""
    for l in data.readlines():
        if state == 0:
            if l == "\n":
                state = 1
                continue
            try:
                if not l.startswith("#"):
                    tag,value = l.split(":")
                    metadata[tag.strip()] = value.strip()
            except:
                state = 1
        if state == 1:
            text += l

    # Metadata Options
    #title: huzzah
    #url:    /index.html
    #sm_f:   daily, hourly
    #sm_p:   0.0-1.0
    #tags:   comma, separated, tags
    #state:  true, publish, draft, false
    #summary:    yada yada yada
    #template:   list of templates to use
    #update_index:   false
    #comments:   false
    #mailinglist

    name = os.path.basename(f)[:-3] # remove .md from end
    if "title" not in metadata:
        metadata["title"] = name
    if not metadata.has_key("template"):
        metadata["template"] = "html"
    if "url" not in metadata:
        metadata["url"] = "/%s/index.html"%name
    if metadata["url"][0] != "/":
        metadata["url"] = "/%s"%metadata["url"]
    metadata["furl"] = "%s%s"%(domain,metadata["url"])
    print metadata["furl"]
    metadata["reverse_links"] = {}

    metadata["filename"] = os.path.join(out,metadata["url"].strip("/"))

    if not "draft" in metadata:
        page[name] = {}
        page[name]["metadata"] = metadata
        page[name]["text"] = text

        logging.debug("Will publish: %s"%name)
    else:
        logging.debug("Not publishing: %s"%name)

for current_page in page.keys():
    logging.debug("Processing page %s"%current_page)
    metadata = page[current_page]["metadata"]
    text = page[current_page]["text"].decode('utf-8',"replace")

    if "comments" in metadata:
        metadata["comments"] = templates["comments"].safe_substitute(metadata)
    else:
        metadata["comments"] = ""

    if "mailinglist" in metadata:
        metadata["mailinglist"] = templates["mailinglist"].safe_substitute(metadata)
    else:
        metadata["mailinglist"] = ""

    try:
        metadata["html"] = md.render(text)
    except Exception as e:
        logging.fatal("Exception while rendering %s, %s"%(current_page, e))
        sys.exit(1)
    metadata["html_tags"] = ""
    if "tags" in metadata:
        metadata["html_tags"] = "<ul id=\"tags\">\n"
        for tag in metadata["tags"].split(","):
            tag = tag.strip()
            if tag != "":
                if tag in page:
                    metadata["html_tags"] = metadata["html_tags"] + "\t<li><a href=\"%s\">%s</a></li>\n"%(page[tag]["metadata"]["url"],page[tag]["metadata"]["title"])
                    # reverse link
                    metadata["reverse_links"][tag] = "tag"
                else:
                    logging.fatal("Tag '%s' is referenced in file '%s' but does not exist. Please create it first!"%(tag,current_page))
                    sys.exit(1)
        metadata["html_tags"] = metadata["html_tags"] + "</ul>\n"

    metadata["output"] = templates[metadata["template"]].safe_substitute(metadata)

# Check all reverse links exist, and warn if absent
for current_page in page.keys():
    for rev_link in page[current_page]["metadata"]["reverse_links"].keys():
        if current_page not in page[rev_link]["metadata"]["reverse_links"]:
            print ("WARNING: %s is linked to by %s, but not in the reverse direction"%(rev_link,current_page))


# Generate all output files including sitemap
sitemap_file= open(os.path.join(out,"sitemap.xml"),"w")
sitemap_file.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n")
for k in page.keys():
    metadata = page[k]["metadata"]
    logging.info("Generated %s, %s"%(k, metadata["filename"]))
    try:os.makedirs(os.path.dirname(metadata["filename"]))
    except: pass
    html_file = open(metadata["filename"],"w")
    html_file.write(metadata["output"].encode("utf-8"))
    html_file.close()

    # Default values for sitemap entries
    try:sm_f = metadata["sm_f"]
    except: sm_f = "weekly"
    try:sm_p = metadata["sm_p"]
    except: sm_p = 0.5

    lastmod = time.strftime('%Y-%m-%dT%H:%M:%S+00:00',time.gmtime(metadata["mod_time"]))
    sitemap_file.write("\t<url>\n\t\t<loc>%s%s</loc>\n\t\t<lastmod>%s</lastmod>\n\t\t<changefreq>%s</changefreq>\n\t\t<priority>%s</priority>\n\t</url>\n"%(domain,metadata["url"],lastmod,sm_f,sm_p))
# close sitemap file
sitemap_file.write("</urlset>")
sitemap_file.close()

commit_msg = "Site updated by waste"
print "Please run the following commands" # Could automate this
print "cd %s\ngit add --all\ngit commit -m \"%s\"\ngit push -u origin master"%(out,commit_msg)
print "curl http://www.google.com/webmasters/tools/ping?sitemap=http%3A%2F%2Fsimonduff.net%2Fsitemap.xml "
print "curl http://www.bing.com/ping?sitemap=http%3A%2F%2Fsimonduff.net%2Fsitemap.xml"

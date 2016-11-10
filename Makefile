
.DEFAULT: meremember

.PHONY: meremember
meremember:
	@echo "targets:"
	@echo "  switching clientsecrets"
	@echo "   > local"
	@echo "   > gae"
	@echo "  setup css and js"
	@echo "   > css"
	@echo "   > js"
	@echo "   > footable"
	@echo "  install python libs"
	@echo "   > libs"
	@echo "  generate templates"
	@echo "   > templates"

all: libs css js footable templates

#------------------------------------------------------------------------------
# switch between local and gae client_secrets
#
.PHONY: local gae
local:
	cp client_secrets.json-local client_secrets.json
gae:
	cp client_secrets.json-gae client_secrets.json

#------------------------------------------------------------------------------
# CREATE minified CSS
#
CSSSRC=css
CSSDEST=static/css
CSSSRCFILES = $(wildcard $(CSSSRC)/*.css)
CSSDESTFILES = $(patsubst $(CSSSRC)/%.css, $(CSSDEST)/%.min.css, $(CSSSRCFILES))

.PHONY: css
css: $(CSSDESTFILES)

$(CSSDEST)/%.min.css: $(CSSSRC)/%.css
	yui-compressor $< -o $@

#------------------------------------------------------------------------------
# CREATE minified JS
#
JSSRC=js
JSDEST=static/js
JSSRCFILES = $(wildcard $(JSSRC)/*.js)
JSDESTFILES = $(patsubst $(JSSRC)/%.js, $(JSDEST)/%.min.js, $(JSSRCFILES))

.PHONY: js
js: $(JSDESTFILES)

$(JSDEST)/%.min.js: $(JSSRC)/%.js
	yui-compressor $< -o $@

#------------------------------------------------------------------------------
# DOWNLOAD FOOTABLE
#
FOOTABLECOMMIT=0d803160d692cd9f043ba0e38b522c9723502b04

.PHONY: footable 
FOOTABLEJS=footable.min.js footable.filter.min.js footable.sort.min.js footable.paginate.min.js
FOOTABLECSS=footable.core.min.css
FOOTABLEFONTS=footable.eot footable.svg footable.ttf footable.woff
.PHONY: $(FOOTABLEJS) $(FOOTABLECSS) $(FOOTABLEFONTS)

$(FOOTABLEJS):
	wget -N https://github.com/bradvin/FooTable/raw/$(FOOTABLECOMMIT)/dist/$@ -P ./static/js/
$(FOOTABLECSS):
	wget -N https://github.com/bradvin/FooTable/raw/$(FOOTABLECOMMIT)/css/$@ -P ./static/css/
$(FOOTABLEFONTS):
	wget -N https://github.com/bradvin/FooTable/raw/$(FOOTABLECOMMIT)/css/fonts/$@ -P ./static/css/fonts/

footable: $(FOOTABLEJS) $(FOOTABLECSS) $(FOOTABLEFONTS)



#------------------------------------------------------------------------------
# DOWNLOAD LIBS
#
LIB=lib
.PHONY: libs
libs:
	pip install -t lib/ -r requirements.txt


#------------------------------------------------------------------------------
# GENERATE web.py templates
#
.PHONY:	templates
templates:
	python $(LIB)/web/template.py --compile ./templates


#------------------------------------------------------------------------------
# DOWNLOAD appengine SDK
#
.PHONY: downloadgaesdk
downloadgaesdk:
	wget http://googleappengine.googlecode.com/files/google_appengine_1.8.8.zip



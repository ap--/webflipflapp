
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
.PHONY: libs
libs: libwebpy libgdata libgae librequests
LIB=lib

WEBPY=web.py-0.37
.PHONY: libwebpy
libwebpy:
	wget -O - http://webpy.org/static/$(WEBPY).tar.gz | tar -xvzf -
	mv $(WEBPY)/web $(LIB)/
	rm -rf $(WEBPY)

GDATA=gdata-2.0.18
.PHONY: libgdata
libgdata:
	wget -O - http://gdata-python-client.googlecode.com/files/$(GDATA).tar.gz  | tar -xvzf -
	mv $(GDATA)/src/* $(LIB)/
	rm -rf $(GDATA)

GAE=google-api-python-client-gae-1.2
.PHONY: libgae
libgae:
	wget http://google-api-python-client.googlecode.com/files/$(GAE).zip
	unzip $(GAE).zip -d $(LIB)/
	rm -f $(GAE).zip

REQUESTS=3327652623415cfa408ef54898071f28e9600ef6
.PHONY: librequests
librequests:
	wget https://github.com/kennethreitz/requests/archive/$(REQUESTS).zip
	unzip $(REQUESTS).zip
	mv requests-$(REQUESTS)/requests $(LIB)/
	rm -f $(REQUESTS).zip
	rm -rf requests-$(REQUESTS)

.PHONY: cleanlibs

cleanlibs:
	rm -rf lib/web
	rm -rf lib/gdata lib/atom
	rm -rf lib/requests
	rm -rf lib/apiclient lib/httplib2 lib/oauth2client lib/uritemplate

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



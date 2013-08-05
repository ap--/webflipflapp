
.DEFAULT: all

.PHONY:	templates css

templates:
	python lib_third_party/web/template.py --compile ./templates

CDIR=static/css
CFILES = $(filter-out $(wildcard $(CDIR)/*.min.css), $(wildcard $(CDIR)/*.css))
CMFILES = $(addsuffix .min.css, $(basename $(CFILES)))

%.min.css: %.css
	curl -X POST -s --data-urlencode 'input@$<' http://cssminifier.com/raw > $@

css: $(CMFILES)

externalcss:
	curl https://raw.github.com/bradvin/FooTable/V2/css/footable.core.min.css > $(CDIR)/footable.core.min.css

JDIR=static/js
externaljs:
	curl https://raw.github.com/bradvin/FooTable/V2/dist/footable.min.js > $(CDIR)/footable.min.js

all: templates css

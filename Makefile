.DEFAULT_GOAL   := all

.PHONY: all
all: compile

.PHONY: compile
compile:
	python setup.py build

.PHONY: install
install: all
	python setup.py install

.PHONY: clean-all
clean-all: clean

.PHONY: clean
clean:
	python setup.py clean
	rm -rf .tox

.PHONY: test
test: check

.PHONY: check
check:
	tox

.PHONY: check-unit
check-unit:
	python setup.py test

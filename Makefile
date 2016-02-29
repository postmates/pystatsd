.DEFAULT_GOAL   := all

.PHONY: all
all: deps compile

.PHONY: compile
compile:
	python setup.py build

.PHONY: clean-all
clean-all: clean

.PHONY: clean
clean:
	python setup.py clean

.PHONY: test
test: check

.PHONY: check
check:
	python -m unittest discover

.PHONY: deps
deps:
	pip install -r requirements.txt

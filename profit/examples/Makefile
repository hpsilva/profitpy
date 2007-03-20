pyuic = pyuic4
pyuicopt = -x -o
objects := $(addsuffix .py, $(basename $(wildcard *.ui)))



.PHONY: all clean full

all: $(objects)


clean:
	rm -f $(objects)
	rm -f *.pyc
	rm -f *.pyo


full: all


$(objects): %.py: %.ui
	$(pyuic) $(pyuicopt) $@ $< 

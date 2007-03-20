.PHONY: all clean full


all:
	cd examples && $(MAKE)
	cd widgets && $(MAKE)


clean:
	rm -f -R *.pyc
	rm -f -R *.pyo
	cd examples && $(MAKE) clean
	cd widgets && $(MAKE) clean


full:
	cd examples && $(MAKE) full
	cd widgets && $(MAKE) full

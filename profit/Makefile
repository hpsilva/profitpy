.PHONY: all clean full


all:
	cd examples && $(MAKE)
	cd widgets && $(MAKE)
	cd neuralnetdesigner && $(MAKE)
	cd strategydesigner && $(MAKE)
	cd workbench && $(MAKE)


clean:
	rm -f -R *.pyc
	rm -f -R *.pyo
	cd examples && $(MAKE) clean
	cd widgets && $(MAKE) clean
	cd neuralnetdesigner && $(MAKE) clean
	cd strategydesigner && $(MAKE) clean
	cd workbench && $(MAKE) clean

full:
	cd examples && $(MAKE) full
	cd widgets && $(MAKE) full
	cd neuralnetdesigner && $(MAKE) full
	cd strategydesigner && $(MAKE) full
	cd workbench && $(MAKE) full


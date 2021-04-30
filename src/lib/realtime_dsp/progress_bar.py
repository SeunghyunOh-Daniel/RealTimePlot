#################################################################################
#                                                                               #
#                              Progress Bar Lib                                 #
#                                                                               #
#################################################################################

'''
	This library provides an easy progress bar implementation for refence in the
	terminal. This function should be called everytime the value needs to be 
	updated, since it only provides the graphical part of the progress bar

	* Params:
	- iteration: the current state (n or i) of the progress
	- total: the total number of interactions
	- prefix: what will be shown before the progress bar (in the same line)
	- suffix: what will be shown after the progress bar (in the same line)
	- decimals: the number of fractional digits shown as progress
	- barLength: the number of characters used in the progress bar

	NOTE: You can edit the function for different characters 

'''

################# Imports #########################
import sys


####################### Functions ############################
def print_progress(iteration, total, prefix='', suffix='', decimals=1, barLength=100):
    formatStr = "{0:." + str(decimals) + "f}"
    percent = formatStr.format(100 * (iteration / float(total)))
    filledLength = int(round(barLength * iteration / float(total)))
    bar = '#' * filledLength + '-' * (barLength - filledLength)
    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percent, '%', suffix)),
    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()

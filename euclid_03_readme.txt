Usage notes:

call parse(...) to convert a code string to an engine object
call mainf(...) with an engine object to start a program
call save_engine(...) to save an engine to a file
call load_engine(...) to load an engine from a file
    warning: load_engine uses python eval(...) and assumes a well-formatted engine file

when a program has been started:
    press A to toggle automatic mode in which the program tries to step 60 times per second
    press H to toggle hyper mode in which the program tries to step 240 times per second
    press M to enter manual mode in which the program tries to step whenever SPACE is pressed
    press SPACE to step the program when in manual mode
when any one of the toggles activate, it sets the other to False.

test_sample, test_calc, test_fibu, and test_dec are all provided as test functions
they access the dictionaries samples, calculators, fizzbuzz, and decimal respectively,
which contain several provided working programs.
test_sample and test_calc optionally accept an input buffer argument to skip the first input request

some sample programs are made very sensitive to the width and height of the program, so watch
their behaviors carefully before attempting to splice it into another program. In order to avoid
using the loop-around behavior, some programs may require additional control paths to allow the
program pointer to navigate entirely within the program.

the program assumes that it is run in some sort of console, and is guaranteed to work in Spyder (for python 3.8+)
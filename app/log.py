# -*- coding: utf-8 -*-

import logging
import os
import types

#-------- Logs setup ----------------------------------------
def new_formatter(self, mode, nbr_newlines=1):
    """Definition of 2 new formats, used for aesthetic reasons

    Parameters
    ----------
    mode : str
        Selects the type of the formatter
    nbr_newlines : int
        Number of empty lines wanted
    """
    if mode == "newline":
        for i in range(len(self.handler)):
            self.handler[i].setFormatter(self.blank_formatter)
        for i in range(nbr_newlines):
            self.info('')
        for i in range(len(self.handler)):
            self.handler[i].setFormatter(self.formatter[i])

    if mode == "end_process":
        for i in range(len(self.handler)):
            self.handler[i].setFormatter(self.blank_formatter)
        self.info('')
        self.info('******************************************')
        self.info('')
        for i in range(len(self.handler)):
            self.handler[i].setFormatter(self.formatter[i])

#------------------------------------------------------------
def setup_logger(name):
    """Logger configuration

    Paramters
    ---------
    name : str
        Name of the file on which we create and call the logger
    """
    logger = logging.getLogger(name)

    logger.setLevel(logging.DEBUG)

    cwd = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(cwd, "../docs/log.log")

    file_handler = logging.FileHandler(path)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%Y %H:%M:%S')
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(fmt='%(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    blank_formatter = logging.Formatter(fmt="")

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.handler = [file_handler, console_handler]
    logger.formatter = [file_formatter, console_formatter]
    logger.blank_formatter = blank_formatter
    logger.new_formatter = types.MethodType(new_formatter, logger)

    return logger
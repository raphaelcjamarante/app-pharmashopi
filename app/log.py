# -*- coding: utf-8 -*-

import logging
import os
import types

import app.utilities

#-------- Logs setup ----------------------------------------
def new_formatter(self, mode, nbr_newlines=1):
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
    logger = logging.getLogger(name)

    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(app.utilities.get_path("docs/log.log"))
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
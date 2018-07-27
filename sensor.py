# Copyright © 2018 Stanislav Hnatiuk.  All rights reserved.

# !/usr/bin/env python3


class Sensor:
    """description of class"""
    # address = ''
    # group = ''
    # name = ''
    # value = 0

    def __init__(self, address, group, name='No name', value=None):
        """__init__(address, group, name='No name', value=None)"""
        self.address = address
        self.name = name
        self.value = value
        self.group = group

    def print(self):
        print(self.value)

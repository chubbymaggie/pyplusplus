# Copyright 2004 Roman Yakovenko.
# Distributed under the Boost Software License, Version 1.0. (See
# accompanying file LICENSE_1_0.txt or copy at
# http://www.boost.org/LICENSE_1_0.txt)

import os
import sys
import unittest
import fundamental_tester_base
from pyplusplus import code_creators 

class unnamed_enums_tester_t(fundamental_tester_base.fundamental_tester_base_t):
    EXTENSION_NAME = 'unnamed_enums'
    
    def __init__( self, *args ):
        fundamental_tester_base.fundamental_tester_base_t.__init__( 
            self
            , unnamed_enums_tester_t.EXTENSION_NAME
            , *args )
                                                                    
    def run_tests(self, module):        
        self.failUnless( module.OK == 1 )
        self.failUnless( module.CANCEL == 0 )

def create_suite():
    suite = unittest.TestSuite()    
    suite.addTest( unittest.makeSuite(unnamed_enums_tester_t))
    return suite

def run_suite():
    unittest.TextTestRunner(verbosity=2).run( create_suite() )

if __name__ == "__main__":
    run_suite()
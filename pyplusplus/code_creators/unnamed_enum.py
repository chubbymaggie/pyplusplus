# Copyright 2004 Roman Yakovenko.
# Distributed under the Boost Software License, Version 1.0. (See
# accompanying file LICENSE_1_0.txt or copy at
# http://www.boost.org/LICENSE_1_0.txt)

import os
import pygccxml
import algorithm
import declaration_based

class unnamed_enum_t( declaration_based.declaration_based_t ):
    def __init__(self, unnamed_enum, parent=None ):
        declaration_based.declaration_based_t.__init__( self
                                                        , parent=parent
                                                        , declaration=unnamed_enum)

    def _get_value_aliases(self):
        return self.declaration.value_aliases
    def _set_value_aliases(self, value_aliases):
        self.declaration.value_aliases = value_aliases
    value_aliases = property( _get_value_aliases, _set_value_aliases )
    
    def _create_impl(self):
        tmpl = algorithm.create_identifier( self, '::boost::python::scope' ) + '().attr("%s") = (int)%s;'
        full_name = pygccxml.declarations.full_name( self.declaration )
        result = []
        for name, value in self.declaration.values.items():
            result.append( tmpl % ( self.value_aliases.get( name, name )
                                    , algorithm.create_identifier( self, full_name + '::' + name ) ) )
        return os.linesep.join( result )

# Copyright 2004 Roman Yakovenko.
# Distributed under the Boost Software License, Version 1.0. (See
# accompanying file LICENSE_1_0.txt or copy at
# http://www.boost.org/LICENSE_1_0.txt)

from pygccxml import declarations
from pyplusplus import decl_wrappers

class manager_t( object ):
    def __init__( self, logger ):
        object.__init__( self )
        self.__exported_decls = []
        self.__logger = logger
        
    def add_exported( self, decl ):
        self.__exported_decls.append( decl )  

    def __is_std_decl( self, decl ):
        if not decl.parent:
            return False

        if not isinstance( decl.parent, declarations.namespace_t ):
            return False

        if 'std' != decl.parent.name:
            return False

        ns_std = decl.parent
        if not ns_std.parent:
            return False

        if not isinstance( ns_std.parent, declarations.namespace_t ):
            return False

        if '::' != ns_std.parent.name:
            return False

        global_ns = ns_std.parent
        if global_ns.parent:
            return False 
        
        if decl.name.startswith( 'pair<' ):
            #special case
            return False
        return True

    def __build_dependencies( self, decl ):
        if self.__is_std_decl( decl ):
            return [] #std declarations should be exported by Py++!
        return decl.i_depend_on_them()
        
    def __find_out_used_but_not_exported( self ):
        used_not_exported = []
        exported_ids = set( map( lambda d: id( d ), self.__exported_decls ) )
        for decl in self.__exported_decls:
            for dependency in self.__build_dependencies( decl ):
                depend_on_decl = dependency.find_out_depend_on_declaration()
                if None is depend_on_decl:
                    continue
                if self.__is_std_decl( depend_on_decl ):
                    continue
                if isinstance( depend_on_decl, declarations.class_types ) and depend_on_decl.opaque:
                    continue
                if id( depend_on_decl ) not in exported_ids:
                    used_not_exported.append( dependency )                    
        return used_not_exported

    def __create_msg( self, dependency ):
        reason = 'The declaration depends on unexposed declaration "%s".' \
              % dependency.find_out_depend_on_declaration()
        return "%s;%s" % ( dependency.declaration, reason )
        
    def inform_user( self ):
        used_not_exported_decls = self.__find_out_used_but_not_exported()
        for used_not_exported in used_not_exported_decls:
            self.__logger.warn( self.__create_msg( used_not_exported ) )

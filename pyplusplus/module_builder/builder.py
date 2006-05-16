# Copyright 2004 Roman Yakovenko.
# Distributed under the Boost Software License, Version 1.0. (See
# accompanying file LICENSE_1_0.txt or copy at
# http://www.boost.org/LICENSE_1_0.txt)

import os
import time
import types
from sets import Set as set
from pygccxml import parser
from pygccxml import declarations as decls_package
from pyplusplus import decl_wrappers
from pyplusplus import module_creator as mcreator_package
from pyplusplus import file_writers
from pyplusplus import _logging_

class module_builder_t(object):
    """
    This class provides users with simple and intuitive interface to pyplusplus
    and/or pygccxml functionality. If this is your first attempt to use pyplusplus
    consider to read tutorials. You can find them on U{web site<http://www.language-binding.net>}.
    """
    
    def __init__( self
                  , files 
                  , gccxml_path='' 
                  , working_directory='.' 
                  , include_paths=None
                  , define_symbols=None
                  , undefine_symbols=None
                  , start_with_declarations=None
                  , compilation_verbose=False
                  , compilation_mode=None
                  , cache=None
                  , optimize_queries=True):
        """
        @param files: list of files, declarations from them you want to export
        @type files: list of strings or L{file_configuration_t} instances
        
        @param gccxml_path: path to gccxml binary. If you don't pass this argument,
        pygccxml parser will try to locate it using you environment PATH variable
        @type gccxml_path: str
        
        @param include_paths: additional header files location. You don't have to
        specify system and standard directories.
        @type include_paths: list of strings
        
        @param define_symbols: list of symbols to be defined for preprocessor.
        @param define_symbols: list of strings
        
        @param undefine_symbols: list of symbols to be undefined for preprocessor.
        @param undefine_symbols: list of strings
        """
        object.__init__( self )
        gccxml_config = parser.config_t( 
            gccxml_path=gccxml_path
            , working_directory=working_directory
            , include_paths=include_paths
            , define_symbols=define_symbols
            , undefine_symbols=undefine_symbols
            , start_with_declarations=start_with_declarations
            , verbose=compilation_verbose)

        #may be in future I will add those directories to user_defined_directories
        #to self.__code_creator.
        self.__working_dir = os.path.abspath( working_directory )

        self.__parsed_files = map( decls_package.filtering.normalize_path
                                   , parser.project_reader_t.get_os_file_names( files ) )
        tmp = map( lambda file_: os.path.split( file_ )[0], self.__parsed_files )
        self.__parsed_dirs = filter( None, tmp )
        
        self.__global_ns = self.__parse_declarations( files
                                                      , gccxml_config
                                                      , compilation_mode
                                                      , cache )
        self.__code_creator = None         
        if optimize_queries:
            self.run_query_optimizer()
        
    def _get_global_ns( self ):
        return self.__global_ns
    global_ns = property( _get_global_ns, doc="reference to global namespace" )
    
    def run_query_optimizer(self):
        """
        It is possible to optimze time that takes to execute queries. In most cases
        this is done from __init__ method. But there are use-case, when you need
        to disable optimizer at __init__ and run it later.
        """
        self.__global_ns.init_optimizer()
    
    def __parse_declarations( self, files, gccxml_config, compilation_mode, cache ):
        if None is gccxml_config:
            gccxml_config = parser.config_t()
        if None is compilation_mode:
            compilation_mode = parser.COMPILATION_MODE.FILE_BY_FILE
        start_time = time.clock()
        _logging_.logger.debug( 'parsing files - started' )
        reader = parser.project_reader_t( gccxml_config, cache, decl_wrappers.dwfactory_t() )
        decls = reader.read_files( files, compilation_mode )
        _logging_.logger.debug( 'parsing files - done( %f seconds )' % ( time.clock() - start_time ) )
        _logging_.logger.debug( 'settings declarations defaults- started' )
        start_time = time.clock()
        self.__apply_decls_defaults(decls)
        _logging_.logger.debug( 'settings declarations defaults - done( %f seconds )'
                                % ( time.clock() - start_time ) )
        return decls_package.matcher.get_single( 
                decls_package.namespace_matcher_t( name='::' )
                , decls )

    def __filter_by_location( self, flatten_decls ):
        for decl in flatten_decls:            
            if not decl.location:
                continue
            fpath = decls_package.filtering.normalize_path( decl.location.file_name )
            if decls_package.filtering.contains_parent_dir( fpath, self.__parsed_dirs ):
                continue
            if fpath in self.__parsed_files:
                continue
            found = False
            for pfile in self.__parsed_files:
                if fpath.endswith( pfile ):
                    found = True
                    break
            if not found:
                decl.exclude()
        
    def __apply_decls_defaults(self, decls):
        flatten_decls = decls_package.make_flatten( decls )
        self.__filter_by_location( flatten_decls )
        call_policies_resolver = mcreator_package.built_in_resolver_t()
        calldefs = filter( lambda decl: isinstance( decl, decls_package.calldef_t )
                           , flatten_decls )
        map( lambda calldef: calldef.set_call_policies( call_policies_resolver( calldef ) )
             , calldefs )
    
    def print_declarations(self, decl=None, detailed=True, recursive=True, writer=sys.stdout.write):
        """
        This function will print detailed description of all declarations or
        some specific one.
        
        @param decl: optional, if passed, then only it will be printed
        @type decl: instance of L{decl_wrappers.decl_wrapper_t} class
        """
        if None is decl:
            decl = self.global_ns
        decl_wrappers.print_declarations( decl, detailed, recursive, writer )
        
    def build_code_creator( self
                       , module_name
                       , boost_python_ns_name='bp'
                       , create_castinig_constructor=True
                       , call_policies_resolver_=None
                       , types_db=None
                       , target_configuration=None ):
        """
        Creates L{module_t} code creator.
        
        @param module_name: module name 
        @type module_name: string
        
        @param boost_python_ns_name: boost::python namespace alias, by default 
        it is 'bp'
        @type boost_python_ns_name: string
        
        @param call_policies_resolver_: callable, that will be invoked on every
        calldef object. It should return call policies.
        @type call_policies_resolver_: callable
        """
        creator = mcreator_package.creator_t( self.global_ns
                                              , module_name
                                              , boost_python_ns_name
                                              , create_castinig_constructor
                                              , call_policies_resolver_
                                              , types_db
                                              , target_configuration )
        self.__code_creator = creator.create()
        #I think I should ask users, what they expect
        #self.__code_creator.user_defined_directories.append( self.__working_dir )
        #map( self.__code_creator.user_defined_directories.append
        #     , self.__parsed_dirs )

        return self.__code_creator
    
    def _get_module( self ):
        if not self.__code_creator:
            raise RuntimeError( "self.module is equal to None. Did you forget to call build_code_creator function?" )
        return self.__code_creator
    code_creator = property( _get_module, doc="reference to L{code_creators.module_t} instance" )
    
    def has_code_creator( self ):
        """
        Function, that will return True if build_code_creator function has been 
        called and False otherwise
        """
        return not ( None is self.__code_creator )
    
    def write_module( self, file_name ):
        """
        Writes module to single file
        @param file_name: file name
        @type file_name: string
        """
        file_writers.write_file( self.code_creator, file_name )
        
    def split_module(self, dir_name):
        """
        Writes module to multiple files
        
        @param dir_name: directory name
        @type dir_name: string
        """
        file_writers.write_multiple_files( self.code_creator, dir_name )

    #select decl(s) interfaces
    def decl( self, name=None, function=None, header_dir=None, header_file=None, recursive=None ):     
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.decl( name=name
                                    , function=function
                                    , header_dir=header_dir
                                    , header_file=header_file
                                    , recursive=recursive)

    def decls( self, name=None, function=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.decls( name=name
                                     , function=function
                                     , header_dir=header_dir
                                     , header_file=header_file 
                                     , recursive=recursive)

    def class_( self, name=None, function=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.class_( name=name
                                      , function=function
                                      , header_dir=header_dir
                                      , header_file=header_file 
                                      , recursive=recursive)

    def classes( self, name=None, function=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.classes( name=name
                                       , function=function
                                       , header_dir=header_dir
                                       , header_file=header_file 
                                       , recursive=recursive)
    
    def variable( self, name=None, function=None, type=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.variable( name=name
                                        , function=function
                                        , type=type
                                        , header_dir=header_dir
                                        , header_file=header_file 
                                        , recursive=recursive)

    def variables( self, name=None, function=None, type=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.variables( name=name
                                         , function=function
                                         , type=type
                                         , header_dir=header_dir
                                         , header_file=header_file 
                                         , recursive=recursive)
    
    def calldef( self, name=None, function=None, return_type=None, arg_types=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.calldef( name=name
                                       , function=function
                                       , return_type=return_type
                                       , arg_types=arg_types 
                                       , header_dir=header_dir
                                       , header_file=header_file 
                                       , recursive=recursive )

    def calldefs( self, name=None, function=None, return_type=None, arg_types=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.calldefs( name=name
                                        , function=function
                                        , return_type=return_type
                                        , arg_types=arg_types 
                                        , header_dir=header_dir
                                        , header_file=header_file
                                        , recursive=recursive)
    
    def operator( self, name=None, symbol=None, return_type=None, arg_types=None, decl_type=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.operator( name=name
                                        , symbol=symbol
                                        , function=function
                                        , decl_type=decl_type
                                        , return_type=return_type
                                        , arg_types=arg_types 
                                        , header_dir=header_dir
                                        , header_file=header_file 
                                        , recursive=recursive )

    def operators( self, name=None, symbol=None, return_type=None, arg_types=None, decl_type=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.operators( name=name
                                         , symbol=symbol
                                         , function=function
                                         , decl_type=decl_type
                                         , return_type=return_type
                                         , arg_types=arg_types 
                                         , header_dir=header_dir
                                         , header_file=header_file 
                                         , recursive=recursive )
                                         
    def member_function( self, name=None, function=None, return_type=None, arg_types=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.member_function( name=name
                                               , function=function
                                               , return_type=return_type
                                               , arg_types=arg_types 
                                               , header_dir=header_dir
                                               , header_file=header_file 
                                               , recursive=recursive )

    def member_functions( self, name=None, function=None, return_type=None, arg_types=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.member_functions( name=name
                                                , function=function
                                                , return_type=return_type
                                                , arg_types=arg_types 
                                                , header_dir=header_dir
                                                , header_file=header_file
                                                , recursive=recursive)
    
    def constructor( self, name=None, function=None, return_type=None, arg_types=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.constructor( name=name
                                           , function=function
                                           , return_type=return_type
                                           , arg_types=arg_types 
                                           , header_dir=header_dir
                                           , header_file=header_file 
                                           , recursive=recursive )

    def constructors( self, name=None, function=None, return_type=None, arg_types=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.constructors( name=name
                                            , function=function
                                            , return_type=return_type
                                            , arg_types=arg_types 
                                            , header_dir=header_dir
                                            , header_file=header_file
                                            , recursive=recursive)
    
    def member_operator( self, name=None, symbol=None, return_type=None, arg_types=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.member_operator( name=name
                                               , symbol=symbol
                                               , function=function
                                               , return_type=return_type
                                               , arg_types=arg_types 
                                               , header_dir=header_dir
                                               , header_file=header_file 
                                               , recursive=recursive )

    def member_operators( self, name=None, symbol=None, return_type=None, arg_types=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.member_operators( name=name
                                                , symbol=symbol
                                                , function=function
                                                , return_type=return_type
                                                , arg_types=arg_types 
                                                , header_dir=header_dir
                                                , header_file=header_file 
                                                , recursive=recursive ) 
    
    def casting_operator( self, name=None, function=None, return_type=None, arg_types=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.casting_operator( name=name
                                                , function=function
                                                , return_type=return_type
                                                , arg_types=arg_types 
                                                , header_dir=header_dir
                                                , header_file=header_file 
                                                , recursive=recursive )

    def casting_operators( self, name=None, function=None, return_type=None, arg_types=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.casting_operators( name=name
                                                 , function=function
                                                 , return_type=return_type
                                                 , arg_types=arg_types 
                                                 , header_dir=header_dir
                                                 , header_file=header_file
                                                 , recursive=recursive)

    def enumeration( self, name=None, function=None, header_dir=None, header_file=None, recursive=None ):     
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.enumeration( name=name
                                           , function=function
                                           , header_dir=header_dir
                                           , header_file=header_file
                                           , recursive=recursive)
    enum = enumeration
    
    def enumerations( self, name=None, function=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.scopedef_t} class documentation"""
        return self.global_ns.enumerations( name=name
                                            , function=function
                                            , header_dir=header_dir
                                            , header_file=header_file 
                                            , recursive=recursive)
                                        
    enums = enumerations
    
    def namespace( self, name=None, function=None, recursive=None ):
        """Please see L{decl_wrappers.namespace_t} class documentation"""
        return self.global_ns.namespace( name=name
                                         , function=function
                                         , recursive=recursive )

    def namespaces( self, name=None, function=None, recursive=None ):
        """Please see L{decl_wrappers.namespace_t} class documentation"""
        return self.global_ns.namespaces( name=name
                                          , function=function
                                          , recursive=recursive )
    
    def free_function( self, name=None, function=None, return_type=None, arg_types=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.namespace_t} class documentation"""
        return self.global_ns.free_function( name=name
                                             , function=function
                                             , return_type=return_type
                                             , arg_types=arg_types 
                                             , header_dir=header_dir
                                             , header_file=header_file 
                                             , recursive=recursive )

    def free_functions( self, name=None, function=None, return_type=None, arg_types=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.namespace_t} class documentation"""
        return self.global_ns.free_functions( name=name
                                              , function=function
                                              , return_type=return_type
                                              , arg_types=arg_types 
                                              , header_dir=header_dir
                                              , header_file=header_file
                                              , recursive=recursive)

    def free_operator( self, name=None, function=None, symbol=None, return_type=None, arg_types=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.namespace_t} class documentation"""
        return self.global_ns.free_operator( name=name
                                             , symbol=symbol
                                             , function=function
                                             , return_type=return_type
                                             , arg_types=arg_types 
                                             , header_dir=header_dir
                                             , header_file=header_file 
                                             , recursive=recursive )

    def free_operators( self, name=None, function=None, symbol=None, return_type=None, arg_types=None, header_dir=None, header_file=None, recursive=None ):
        """Please see L{decl_wrappers.namespace_t} class documentation"""
        return self.global_ns.free_operators( name=name
                                              , symbol=symbol
                                              , function=function
                                              , return_type=return_type
                                              , arg_types=arg_types 
                                              , header_dir=header_dir
                                              , header_file=header_file 
                                              , recursive=recursive )

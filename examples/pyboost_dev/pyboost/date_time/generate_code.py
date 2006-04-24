#! /usr/bin/python
# Copyright 2004 Roman Yakovenko.
# Distributed under the Boost Software License, Version 1.0. (See
# accompanying file LICENSE_1_0.txt or copy at
# http://www.boost.org/LICENSE_1_0.txt)


import os
import sys
import time
import shutil
from environment import settings
from pygccxml import parser
from pygccxml import declarations
from pyplusplus import code_creators
import customization_data
from pyplusplus import module_builder

class exporter_t(object):    
    def __init__(self):
        self.__file = os.path.join( settings.date_time_pypp_include, 'date_time.pypp.hpp' )                        

    def _create_xml_file( self ):
        #On windows I have some problems to compile boost.date_time
        #library, so I use xml files generated on linux
        config = parser.config_t( gccxml_path=settings.gccxml_path
                                  , include_paths=[settings.boost_path]
                                  , define_symbols=settings.defined_symbols
                                  , undefine_symbols=settings.undefined_symbols )

        reader = parser.source_reader_t( config )
        destination = os.path.join( settings.date_time_pypp_include, 'date_time.pypp.xml' )
        if sys.platform == 'linux2':
            reader.create_xml_file( self.__file, destination )
        return destination
    
    def create_module_builder(self):
        date_time_xml_file = self._create_xml_file()
        mb = module_builder.module_builder_t( [ parser.create_gccxml_fc( date_time_xml_file ) ]
                                              , gccxml_path=settings.gccxml_path
                                              , include_paths=[settings.boost_path]
                                              , define_symbols=settings.defined_symbols
                                              , undefine_symbols=settings.undefined_symbols
                                              , optimize_queries=False)
        if sys.platform == 'win32':
            linux_name = "time_duration<boost::posix_time::time_duration,boost::date_time::time_resolution_traits<boost::date_time::time_resolution_traits_adapted64_impl, micro, 1000000, 6, int> >"
            win_name = "time_duration<boost::posix_time::time_duration,boost::date_time::time_resolution_traits<boost::date_time::time_resolution_traits_adapted64_impl, micro, 1000000, 6, long int> >"
            time_duration_impl = mb.class_( linux_name )            
            #small price for generating code from xml and not from sources
            time_duration_impl.name = win_name

        mb.run_query_optimizer()
        
        for name, alias in customization_data.name2alias.items():
            decl = mb.class_( name )
            s = set( map( lambda typedef: typedef.name, decl.typedefs ) )
            if len( s ) > 1:
                print '====> aliases: ', s 
            decl.alias = alias
            if isinstance( decl, declarations.class_t ):
                decl.wrapper_alias = alias + '_wrapper'

        return mb
    
    def filter_declarations(self, mb ):
        mb.global_ns.exclude()
        mb.global_ns.namespace( 'pyplusplus', recursive=False ).include()
        boost_ns = mb.global_ns.namespace( 'boost', recursive=False )
        boost_ns.namespace( 'posix_time', recursive=False ).include()
        boost_ns.namespace( 'date_time', recursive=False ).include()
        boost_ns.namespace( 'gregorian', recursive=False ).include()
        boost_ns.namespace( 'local_time', recursive=False ).include()
        boost_ns.classes( lambda decl: decl.name.startswith( 'constrained_value<' ) ).include()
                
        to_be_removed = [ 'month_str_to_ushort', 'from_stream_type', 'parse_date' ]
        boost_ns.calldefs( lambda decl: decl.name in to_be_removed ).exclude()

        to_be_removed = [ 'c_time'
                          , 'duration_traits_long'
                          , 'duration_traits_adapted'
                          , 'posix_time_system_config' #TODO find out link bug
                          , 'millisec_posix_time_system_config' ]
        boost_ns.classes( lambda decl: decl.name in to_be_removed ).exclude()
        
        starts_with = [ 'time_resolution_traits<'
                        , 'counted_time_rep<'
                        , 'date_facet<'
                        , 'period_formatter<'
                        , 'date_generator_formatter<'
                        , 'special_values_formatter<' ]       
        for name in starts_with:
            boost_ns.classes( lambda decl: decl.name.startswith( name ) ).exclude()
                
        ends_with = [ '_impl', '_config']
        for name in ends_with:
            boost_ns.classes( lambda decl: decl.name.endswith( name ) ).exclude()        

        #boost.date_time has problem to create local_[micro]sec_clock
        #variable, it has nothing to do with pyplusplus
        empty_classes = ['local_microsec_clock', 'local_sec_clock']
        for alias in empty_classes:
            class_ = boost_ns.class_( lambda decl: decl.alias == alias )
            class_.exclude()
            class_.ignore = False
        
        for alias in [ 'microsec_clock', 'second_clock' ]:
            class_ = boost_ns.class_( lambda decl: decl.alias == alias )
            class_.calldefs().create_with_signature = True
            
        tdi = mb.class_( lambda decl: decl.alias == 'time_duration_impl' )
        tdi_init = tdi.constructor( arg_types=[None, None, None, None], recursive=False)
        tdi_init.ignore=True


    def fix_free_template_functions(self, mb):
        boost_ns = mb.global_ns.namespace( 'boost', recursive=False )
        boost_ns.free_functions().create_with_signature = True
        
        #This function fixes some boost.date_time function signatures
        tmpl_on_return_type = [ 'parse_iso_time'
                                 , 'parse_undelimited_time_duration'
                                 , 'parse_delimited_time' 
                                 , 'parse_delimited_time_duration'
                                 , 'parse_undelimited_date'
                                 , 'str_from_delimited_time_duration']
        functions = boost_ns.free_functions( lambda decl: decl.name in tmpl_on_return_type )
        for function in functions:
            function.alias = function.name
            function.name = declarations.templates.join( function.name
                                                         , [ function.return_type.decl_string ] )
            
        #template on second argument
        functions = boost_ns.free_functions( 'from_simple_string_type' )
        functions.create_with_signature = False
        for function in functions:
            function.alias = function.name
            return_args = declarations.templates.split( function.return_type.decl_string )[1]
            args = [ return_args[0] ]
            if 'wchar_t' in function.arguments[0].type.decl_string:
                args.append( 'wchar_t' )
            else:
                args.append( 'char' )
            function.name = declarations.templates.join( function.name, args )
            
        tmpl_on_char_type = [ 'to_iso_extended_string_type'
                              , 'to_iso_string_type' 
                              , 'to_simple_string_type' 
                              , 'to_sql_string_type' ]

        functions = boost_ns.free_functions( lambda decl: decl.name in tmpl_on_char_type )
        for function in functions:
            function.alias = function.name
            args = []
            if 'wchar_t' in function.return_type.decl_string:
                args.append( 'wchar_t' )
                function.alias = function.alias + '_w'
            else:
                args.append( 'char' )
            function.name = declarations.templates.join( function.name, args )

    def replace_include_directives( self, mb ):
        extmodule = mb.code_creator
        includes = filter( lambda creator: isinstance( creator, code_creators.include_t )
                           , extmodule.creators )
        includes = includes[1:] #all includes except boost\python.hpp
        map( lambda creator: extmodule.remove_creator( creator ), includes )
        for include_header in customization_data.includes:            
            extmodule.adopt_include( code_creators.include_t( header=include_header ) )

    def add_code( self, mb ):
        as_number_template = 'def( "as_number", &%(class_def)s::operator %(class_def)s::value_type, bp::default_call_policies() )'
        
        classes = mb.classes()
        classes.always_expose_using_scope = True #better error reporting from compiler

        classes = mb.classes(lambda decl: decl.alias != 'local_date_time' )
        classes.redefine_operators = True #redefine all operators found in base classes
        
        classes = mb.classes(lambda decl: decl.name.startswith('constrained_value<') )
        for cls in classes:
            cls.add_code( as_number_template % { 'class_def' : declarations.full_name( cls ) } )

        classes = mb.classes(lambda decl: decl.alias in [ 'date_duration', 'time_duration' ] )
        for operator in [ '>', '>=', '<=', '<', '+', '-' ]:
            classes.add_code( 'def( bp::self %s  bp::self )' % operator )

        ptime = mb.class_( lambda decl: decl.alias == 'ptime' )
        for operator in [ '>', '>=', '<=', '<', '-' ]:
            ptime.add_code( 'def( bp::self %s  bp::self )' % operator )
                
    def beautify_code( self, mb ):
        extmodule = mb.code_creator
        position = extmodule.last_include_index() + 1
        extmodule.adopt_creator( code_creators.namespace_using_t( 'boost' )
                                 , position )
        position += 1
        extmodule.adopt_creator( code_creators.namespace_using_t( 'boost::date_time' )
                                 , position )
        position += 1
        
        for full_ns_name, alias in customization_data.ns_aliases.items():
            creator = code_creators.namespace_alias_t( alias=alias
                                                       , full_namespace_name=full_ns_name )
            extmodule.adopt_creator( creator, position )
            position += 1

    def customize_extmodule( self, mb ):
        extmodule = mb.code_creator
        #beautifying include code generation
        extmodule.license = customization_data.license
        extmodule.user_defined_directories.append( settings.boost_path )
        extmodule.user_defined_directories.append( settings.working_dir )
        extmodule.user_defined_directories.append( settings.generated_files_dir )
        extmodule.license = customization_data.license
        extmodule.precompiled_header = 'boost/python.hpp'
        self.replace_include_directives( mb )
        self.beautify_code( mb )
        
    def write_files( self, mb ):
        mb.split_module( settings.generated_files_dir )
        shutil.copyfile( os.path.join( settings.date_time_pypp_include, 'date_time_wrapper.hpp' )
                         , os.path.join( settings.generated_files_dir, 'date_time_wrapper.hpp' ) )

    def create(self):
        start_time = time.clock()      
        mb = self.create_module_builder()
        self.filter_declarations(mb)
        self.fix_free_template_functions( mb )      
        self.add_code( mb )        
        
        mb.build_code_creator( settings.module_name )
        
        self.customize_extmodule( mb )
        self.write_files( mb )
        print 'time taken : ', time.clock() - start_time, ' seconds'

def export():
    exporter = exporter_t()
    exporter.create()

if __name__ == '__main__':
    export()
    print 'done'
    
    

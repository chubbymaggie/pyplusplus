// This file has been generated by pyplusplus.

// Copyright 2004 Roman Yakovenko.
// Distributed under the Boost Software License, Version 1.0. (See
// accompanying file LICENSE_1_0.txt or copy at
// http://www.boost.org/LICENSE_1_0.txt)

#include "boost/python.hpp"
#ifdef _MSC_VER
    #pragma hdrstop
#endif //_MSC_VER

#include "unittests/data/class_order4_to_be_exported.hpp"

namespace bp = boost::python;

BOOST_PYTHON_MODULE(class_order4){
    if( true ){
        typedef bp::class_< class_order4::container > container_exposer_t;
        container_exposer_t container_exposer = container_exposer_t( "container" );
        bp::scope container_scope( container_exposer );
        bp::enum_<class_order4::container::fruits>("fruits")
            .value("orange", class_order4::container::orange)
            .value("apple", class_order4::container::apple)
            .export_values()
            ;
        container_exposer.def( bp::init< >()[bp::default_call_policies()] );
        container_exposer.def( bp::init< int, bp::optional< class_order4::container::fruits > >(( bp::arg("arg0"), bp::arg("x")=::class_order4::container::apple ))[bp::default_call_policies()] );
        container_exposer.def_readwrite( "my_fruit", &class_order4::container::my_fruit );
    }
}

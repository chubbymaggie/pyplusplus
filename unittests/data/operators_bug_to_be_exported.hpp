// Copyright 2004 Roman Yakovenko.
// Distributed under the Boost Software License, Version 1.0. (See
// accompanying file LICENSE_1_0.txt or copy at
// http://www.boost.org/LICENSE_1_0.txt)

#ifndef __operators_bug_to_be_exported_hpp__
#define __operators_bug_to_be_exported_hpp__

namespace operators_bug{

template< typename derived_type, typename value_type >
struct number{
    
    value_type value;
    
    friend derived_type operator+( const derived_type& y, const derived_type& x ){ 
        derived_type tmp;
        tmp.value = y.value + x.value; 
        return tmp;
    }
protected:    
    bool operator==( const derived_type& other ){ return value == other.value; }
};

struct integral : public number< integral, int >{
    integral operator+( int x ){
        integral tmp;
        tmp.value = value + x; 
        return tmp;
    }
};

struct integral2 : public number< integral, int >{
    //in this case no operator should be redefined
};

}
    

#endif//__operators_bug_to_be_exported_hpp__

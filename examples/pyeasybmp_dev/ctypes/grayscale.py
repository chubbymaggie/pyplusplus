#! /usr/bin/python
# Copyright 2004-2008 Roman Yakovenko.
# Distributed under the Boost Software License, Version 1.0. (See
# accompanying file LICENSE_1_0.txt or copy at
# http://www.boost.org/LICENSE_1_0.txt)

import sys
import easybmp as pyeasybmp


def grayscale_example(source, target):
    bmp = pyeasybmp.BMP()
    if not bmp.ReadFromFile( source ):
        raise RuntimeError( "Unable to read .bmp file %s" % source )

    print 'width    : ', bmp.TellWidth()
    print 'height   : ', bmp.TellHeight()
    print 'bit depth: ', bmp.TellBitDepth()
    print 'number of colors: ', bmp.TellNumberOfColors()

    byte = lambda x: 255 & x

    for j in range( bmp.TellHeight() ):
        for i in range( bmp.TellWidth() ):
            temp = pyeasybmp.IntSquare( bmp.GetPixel(i,j).Red ) \
                   + pyeasybmp.IntSquare( bmp.GetPixel(i,j).Green ) \
                   + pyeasybmp.IntSquare( bmp.GetPixel(i,j).Blue )
            temp = int( math.floor( math.sqrt( temp / 3.0 ) ) )
            bmp.GetPixel(i,j).Red = byte( temp )
            bmp.GetPixel(i,j).Green = byte( temp )
            bmp.GetPixel(i,j).Blue = byte( temp )

    if bmp.TellBitDepth() < 24:
        pyeasybmp.CreateGrayscaleColorTable( bmp )

    bmp.WriteToFile( target )

if __name__ == "__main__":
    if 1 == len( sys.argv ):
        print 'not enough arguments. first arg is source bmp, second is target bmp'
        print 'entering demo mode'
        sys.argv.append( './source.bmp' )
        sys.argv.append( './target.bmp' )
    grayscale_example( sys.argv[1], sys.argv[2] )

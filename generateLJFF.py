#!/usr/bin/python
import sys
import numpy as np
import os
import __main__ as main


import pyProbeParticle                as PPU     
from   pyProbeParticle            import basUtils
from   pyProbeParticle            import elements   
import pyProbeParticle.GridUtils      as GU
#import pyProbeParticle.core          as PPC
import pyProbeParticle.HighLevel      as PPH
import pyProbeParticle.fieldFFT       as fFFT
import pyProbeParticle.cpp_utils      as cpp_utils

HELP_MSG="""Use this program in the following way:
%s -i <filename> 

Supported file formats are:
   * xyz 
""" %os.path.basename(main.__file__)


from optparse import OptionParser

parser = OptionParser()
parser.add_option( "-i", "--input", action="store", type="string", help="format of input file")
parser.add_option( "-q", "--charge" , action="store_true", default=False, help="Electrostatic forcefield from Q nearby charges ")
parser.add_option( "--noPBC", action="store_false",  help="pbc False", default=True)
parser.add_option( "-E", "--energy", action="store_true",  help="pbc False", default=False)
parser.add_option( "--npy" , action="store_true" ,  help="load and save fields in npy instead of xsf"     , default=False)
(options, args) = parser.parse_args()
opt_dict = vars(options)
    
print options

data_format ="npy" if options.npy else "xsf"

if options.input==None:
    sys.exit("ERROR!!! Please, specify the input file with the '-i' option \n\n"+HELP_MSG)

print " >> OVEWRITING SETTINGS by params.ini  "
PPU.loadParams( 'params.ini' )

print "--- Compute Lennard-Jones Force-filed ---"

atoms, lvec = PPH.importGeometries( options.input )

FFparams=None
if os.path.isfile( 'atomtypes.ini' ):
	print ">> LOADING LOCAL atomtypes.ini"  
	FFparams=PPU.loadSpecies( 'atomtypes.ini' ) 
else:
	FFparams = PPU.loadSpecies( cpp_utils.PACKAGE_PATH+'/defaults/atomtypes.ini' )


iZs,Rs,Qs=PPH.parseAtoms(atoms, autogeom = False, PBC = options.noPBC,
                         FFparams=FFparams )
# This function returns the following information:
# iZs - 1D array, containing the numbers of the elements, which corresponds to
# their position in the atomtypes.ini file (Number of line - 1)
# Rs  - 2D array, containing the coordinates of the atoms:
#       [ [x1,y1,z1],
#         [x2,y2,z2],
#          ... 
#         [xn,yn,zn]]
# Qs  - 1D array, containing the atomic charges

FFLJ, VLJ=PPH.computeLJ( Rs, iZs, FFLJ=None, FFparams=FFparams, Vpot=options.energy )
# This function computes the LJ forces experienced by the ProbeParticle
# FFparams either read from the local "atomtypes.ini" file, or will be read from
# the default one inside the computeLJ function


GU.limit_vec_field( FFLJ, Fmax=10.0 ) # remove too large valuesl; keeps the same direction; good for visualization 


print "--- Save  ---"
GU.save_vec_field( 'FFLJ', FFLJ, lvec,data_format=data_format)
if options.energy :
	Vmax = 10.0; VLJ[ VLJ>Vmax ] = Vmax
	GU.save_scal_field( 'VLJ', VLJ, lvec,data_format=data_format)


if opt_dict["charge"]:
    print "Electrostatic Field from xyzq file"
    FFel, VeL = PPH.computeCoulomb( Rs, Qs, FFel=None, Vpot=options.energy  )
    print "--- Save ---"
    GU.save_vec_field('FFel', FFel, lvec, data_format=data_format)
    if options.energy :
	Vmax = 10.0; Vel[ Vel>Vmax ] = Vmax
	GU.save_scal_field( 'Vel', Vel, lvec, data_format=data_format)

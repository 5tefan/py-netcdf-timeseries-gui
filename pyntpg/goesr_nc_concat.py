#!/usr/bin/env python

import logging
import shutil
from netCDF4 import Dataset as NCDataset
from nco import Nco

EXIT_FAIL = 1

logger = logging.getLogger(__name__)
logger.setLevel( logging.DEBUG )

""" goes_nc_concat.py: Concatenates multiple NetCDF files to a single NetCDF object / file. """


def goesr_nc_concat(fn_list, fn_concat=None, read_only=True, global_attrs=None, debug=False):
    """ Returns a NetCDF object representing a concatenation of multiple files using NCO bindings.

    Args:
        fn_list (list): List of files.
            e.g.: ['OR_SEIS-L1b-MPSL_G16_20032991650000_20032991650290_20151252148107.nc',
                   'OR_SEIS-L1b-MPSL_G16_20032991650300_20032991650590_20151252148107.nc']

    Keyword Args:
        fn_concat (string): Optionally save new NetCDF file permanently to this path (relative is ok).
            e.g.: '/tmp/test_goesr_nc_concat.nc'

        read_only (True): Only effective if 'fn_concat' supplied. True: returned NC object is writable.
            False: returned NC object is read only.

        global_attrs (list): Returns list of global attributes for each file concatenated. This is
            a temporary step toward figuring out what to do with time varying global attributes.

        debug (True): True: print debug on STDOUT. False: no STDOUT.

    Returns:
        NetCDF object reference to aggregated result.
        None if an exception occurs.

    Examples (also, see main() below):
        1) Get MPS-LO:
            >>> from common.goesr import goes_nc_concat            >>> import glob, numpy as np
            >>> fn_list = sorted( glob.glob(
            ...     'OR_SEIS-L1b-MPSL_G??_??????????????_??????????????_??????????????.nc') )
            >>> nc_all = goes_nc_concat.goesr_nc_concat( fn_list, debug=True )

        2) Print Global Attributes:
            >>> print( 'Global Attributes:' )
            >>> nc_all_dict = nc_all.__dict__
            >>> for attr in nc_all_dict: print( '\t%s: %s' % (attr, nc_all_dict[ attr ]) )

        3) Save concatenation to file system permanently:
            >>> fn_concat = '/tmp/test_goesr_nc_concat.nc'
            >>> nc_all = goesr_nc_concat.goesr_nc_concat( fn_list, fn_concat=fn_concat, debug=True )

        4) Use data:
            >>> print( 'Mean Diff-e-flux: %f, %s' %
            ...     ( np.mean( nc_all.variables['DiffElectronFluxes'] ),
            ...     nc_all.variables['DiffElectronFluxes'].units ) )

    Authors: R. Redmon (NOAA/NCEI),

    """

    # TODO: Handle time varying global attributes. As sidecar dictionary? As new variables in returned object?

    # CONFIG
    file_rw_access = 'r' if read_only else 'r+'  # Read Only or Writable?

    if 0 == len(fn_list):
        return None

    # Concatenate to a Temporary File
    nco = Nco()
    fn_tmp = nco.ncrcat(input=fn_list, options='--create_ram')
    logger.debug('Aggregated %d files to temporary file: %s' % (len(fn_list), fn_tmp))

    # Save Temporary File Permanently (User Choice)
    if fn_concat is not None:
        shutil.copy2(fn_tmp, fn_concat)
        logger.debug('Saved aggregated file permanently as: %s' % fn_concat)
        fn_tmp = fn_concat

    # Open Concatenate as netcdf4-python::Dataset
    nc_all = NCDataset(fn_tmp, file_rw_access)

    # Keep Global Attributes as Ordered List (User Choice)
    if global_attrs is not None:
        for fn in fn_list:
            global_attrs.append(NCDataset(fn).__dict__)

    # Return NC Object Reference
    return nc_all


def main():
    """ Demonstrates the basic functionality of concatenating NetCDFs using NCO bindings.
    """

    import glob, numpy as np, sys

    for what in ['MPS-LO', 'MPS-HI', 'Fe093', 'SGPS', 'MAG', 'EXIS-SFXR', 'EXIS-SFEU']:
        print('---------------------------- %s ----------------------------' % what)

        ' MPS-LO file list '
        if what == 'MPS-LO':
            fn_list = sorted(
                glob.glob('OR_SEIS-L1b-MPSL_G??_??????????????_??????????????_??????????????.nc'))

        ' MPS-HI file list '
        if what == 'MPS-HI':
            fn_list = sorted(
                glob.glob('OT_SEIS-L1b-MPSH_G??_s??????????????_e??????????????_c??????????????.nc'))

        ' Fe093 file list OT_SUVI-L1b-Fe093_G16_s20150192116350_e20150192116350_c20150192117009.nc '
        if what == 'Fe093':
            fn_list = sorted(
                glob.glob('OT_SUVI-L1b-Fe093_G??_s??????????????_e??????????????_c??????????????.nc'))

        ' SGPS file list '
        if what == 'SGPS':
            fn_list = sorted(
                glob.glob('OT_SEIS-L1b-SGPS_G??_s??????????????_e??????????????_c??????????????.nc'))

        ' MAG file list '
        if what == 'MAG':
            fn_list = sorted(
                glob.glob('OR_MAG-L1blinear-GEOF_G??_s??????????????_e??????????????_c??????????????.nc'))

        ' EXIS SFXR file list '
        if what == 'EXIS-SFXR':
            fn_list = sorted(
                glob.glob('OT_EXIS-L1b-SFXR_G??_s??????????????_e??????????????_c??????????????.nc'))

        ' EXIS SFEU file list '
        if what == 'EXIS-SFEU':
            fn_list = sorted(
                glob.glob('OT_EXIS-L1b-SFEU_G??_s??????????????_e??????????????_c??????????????.nc'))

        print('Found %d files:' % len(fn_list))
        print(fn_list)
        if not len(fn_list):
            continue

        ' Optional: Save concatenation permanently to user chosen file: '
        fn_concat = '/tmp/test_goesr_nc_concat.nc'

        ' Optional: Return list of global attributes (one dictionary per file): '
        global_attrs = []

        ' Get concatenated data set: '
        nc_all = goesr_nc_concat.goesr_nc_concat(
            fn_list, fn_concat=fn_concat, global_attrs=global_attrs, debug=True)
        if not nc_all:
            print('Concatenation failed.')
            sys.exit(1)

        ' Print Global Attributes '
        print('\nGlobal Attributes:')
        nc_all_dict = nc_all.__dict__
        for attr in nc_all_dict: print('\t%s: %s' % (attr, nc_all_dict[attr]))

        ' Print Dimensions '
        print('\nDimensions:')
        for dim in nc_all.dimensions: print('\t%s: %d' % (dim, len(nc_all.dimensions[dim])))

        ' Print Variable Meta '
        print('\nVariables:')
        for var in nc_all.variables:
            try:
                # TODO: Ugly; clean this up.
                t_units = nc_all.variables[var].units
                t_mean = str(np.mean(nc_all.variables[var]))
                t_std = str(np.std(nc_all.variables[var]))
            except:
                t_units = t_mean = t_std = ''
            print('\t%s: units: %s, dtype: %s, shape: %s, mean: %s, std: %s' % (
                var, t_units, str(nc_all.variables[var].dtype),
                str(nc_all.variables[var].shape), t_mean, t_std))


if __name__ == "__main__":
    main()

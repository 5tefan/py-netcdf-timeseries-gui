#!/usr/bin/env python

""" goesr_nc_concat.py: Concatenates multiple NetCDF files to a single NetCDF object / file. """


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
            >>> import glob, numpy as np, pyntpg.goesr_nc_concat as goesr_nc_concat
            >>> fn_list = sorted( glob.glob(
            ...     'OR_SEIS-L1b-MPSL_G??_??????????????_??????????????_??????????????.nc') )
            >>> nc_all = goesr_nc_concat.goesr_nc_concat( fn_list, debug=True )

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
    # TODO: Replace STDOUT debug with logger.

    ' CONFIG '
    my_name = 'goesr_nc_concat'
    file_rw_access = 'r' if read_only else 'r+'  # Read Only or Writable?

    if 0 == len(fn_list): return None

    ' Imports '
    import shutil
    from netCDF4 import Dataset as NCDataset
    from nco import Nco

    ' Concatenate to a Temporary File '
    nco = Nco()
    fn_tmp = nco.ncrcat(input=fn_list, options='--ram_all')
    if debug: print(my_name + ': Aggregated %d files to temporary file: %s' % (len(fn_list), fn_tmp))

    ' Save Temporary File Permanently (User Choice) '
    if fn_concat is not None:
        shutil.copy2(fn_tmp, fn_concat)
        if debug: print(my_name + ': Saved aggregated file permanently as: %s' % fn_concat)
        fn_tmp = fn_concat

    ' Open Concatenate as netcdf4-python::Dataset '
    nc_all = NCDataset(fn_tmp, file_rw_access)

    ' Keep Global Attributes as Ordered List (User Choice) '
    if global_attrs is not None:
        for fn in fn_list:
            global_attrs.append(NCDataset(fn).__dict__)

    ' Return NC Object Reference '
    return nc_all

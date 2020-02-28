# -*- coding: utf-8 -*-

# import stdlib modules
import os
import importlib
from retrying import retry
import logging
from ost.errors import GPTRuntimeError
from os.path import join as opj
from ost.helpers import helpers as h

logger = logging.getLogger(__name__)

@retry(stop_max_attempt_number=3, wait_fixed=1)
def calibration(infile, outfile, logfile, calibrate_to, ncores=os.cpu_count()):

    # transform calibration parameter to snap readable
    sigma0, beta0, gamma0 = 'false', 'false', 'false'
    
    if calibrate_to is 'gamma0':
        gamma0 = 'true'
    elif calibrate_to is 'beta0':
        beta0 = 'true'
    elif calibrate_to is 'sigma0':
        sigma0 = 'true'
        
    # get path to SNAP's command line executable gpt
    gpt_file = h.gpt_path()

    logger.info('Calibrating the product to {}.'.format(calibrate_to))
    # contrcut command string
    
    command = ('{} Calibration -x -q {}'
                   ' -PoutputBetaBand=\'{}\''
                   ' -PoutputGammaBand=\'{}\''
                   ' -PoutputSigmaBand=\'{}\''
                   ' -t \'{}\' \'{}\''.format(
                          gpt_file, ncores,
                          beta0, gamma0, sigma0,
                          outfile, infile)
    )
    
    # run command and get return code
    return_code = h.run_command(command, logfile)

    # hadle errors and logs
    if return_code == 0:
        logger.info('Calibration to {} successful.'.format(calibrate_to))
    else:
        print(' ERROR: Calibration exited with an error. \
                See {} for Snap Error output'.format(logfile))

    return return_code


@retry(stop_max_attempt_number=3, wait_fixed=1)
def multi_look(infile, outfile, logfile, rg_looks, az_looks, ncores=os.cpu_count()):

    # get path to SNAP's command line executable gpt
    gpt_file = h.gpt_path()

    logger.info('Multi-looking the image with {} looks in'
          ' azimuth and {} looks in range.'.format(az_looks, rg_looks))
    
    # construct command string
    command = ('{} Multilook -x -q {}'
                ' -PnAzLooks={}'
                ' -PnRgLooks={}'
                ' -t \'{}\' {}'.format(
                        gpt_file, ncores,
                        az_looks, rg_looks,
                        outfile, infile
                        )
    )

    # run command and get return code
    return_code = h.run_command(command, logfile)

    # handle errors and logs
    if return_code == 0:
        logger.info('Succesfully multi-looked product.')
    else:
        print(' ERROR: Multi-look exited with an error. \
                See {} for Snap Error output'.format(logfile))

    return return_code


@retry(stop_max_attempt_number=3, wait_fixed=1)
def speckle_filter(infile, outfile, logfile, speckle_dict, ncores=os.cpu_count()):

    """ Wrapper around SNAP's peckle Filter function

    This function takes OST imported Sentinel-1 product and applies
    a standardised version of the Lee-Sigma Speckle Filter with
    SNAP's defaut values.

    Args:
        infile: string or os.path object for
                an OST imported frame in BEAM-Dimap format (i.e. *.dim)
        outfile: string or os.path object for the output
                 file written in BEAM-Dimap format
        logfile: string or os.path object for the file
                 where SNAP'S STDOUT/STDERR is written to
        ncores (int): number of cpus used - useful for parallel processing
    """

    # get path to SNAP's command line executable gpt
    gpt_file = h.gpt_path()

    logger.info('Applying speckle filtering.')
    # contrcut command string
    command = ('{} Speckle-Filter -x -q {}'
                  ' -PestimateENL=\'{}\''
                  ' -PanSize=\'{}\''
                  ' -PdampingFactor=\'{}\''
                  ' -Penl=\'{}\''
                  ' -Pfilter=\'{}\''
                  ' -PfilterSizeX=\'{}\''
                  ' -PfilterSizeY=\'{}\''
                  ' -PnumLooksStr=\'{}\''
                  ' -PsigmaStr=\'{}\''
                  ' -PtargetWindowSizeStr=\"{}\"'
                  ' -PwindowSize=\"{}\"'
                  ' -t \'{}\' \'{}\''.format(
                      gpt_file, ncores,
                      speckle_dict['estimate_ENL'],
                      speckle_dict['pan_size'],
                      speckle_dict['damping'],
                      speckle_dict['ENL'],
                      speckle_dict['filter'],
                      speckle_dict['filter_x_size'],
                      speckle_dict['filter_y_size'],
                      speckle_dict['num_of_looks'],
                      speckle_dict['sigma'],
                      speckle_dict['target_window_size'],
                      speckle_dict['window_size'],
                      outfile, infile)
              )

    # run command and get return code
    return_code = h.run_command(command, logfile)

    # hadle errors and logs
    if return_code == 0:
        logger.info('Successfully applied speckle filtering.')
    else:
        raise GPTRuntimeError(
            'ERROR: Speckle filtering exited with an error {}. See {} for '
            'Snap Error output'.format(return_code, logfile)
        )


@retry(stop_max_attempt_number=3, wait_fixed=1)
def linear_to_db(infile, outfile, logfile, ncores=os.cpu_count()):
    '''A wrapper around SNAP's linear to db routine

    This function takes an OST calibrated Sentinel-1 product
    and converts it to dB.

    Args:
        infile: string or os.path object for
                an OST imported frame in BEAM-Dimap format (i.e. *.dim)
        outfile: string or os.path object for the output
                 file written in BEAM-Dimap format
        logfile: string or os.path object for the file
                 where SNAP'S STDOUT/STDERR is written to
        ncores (int): number of cpus used - useful for parallel processing
    '''

    # get path to SNAP's command line executable gpt
    gpt_file = h.gpt_path()

    logger.info('Converting the image to dB-scale.')
    # construct command string
    command = '{} LinearToFromdB -x -q {} -t \'{}\' {}'.format(
        gpt_file, ncores, outfile, infile)

    # run command and get return code
    return_code = h.run_command(command, logfile)

    # handle errors and logs
    if return_code == 0:
        logger.info('Succesfully converted product to dB-scale.')
    else:
        raise GPTRuntimeError(
            'ERROR: dB Scaling exited with an error {}. See {} for '
            'Snap Error output'.format(return_code, logfile)
        )


@retry(stop_max_attempt_number=3, wait_fixed=1)
def terrain_correction(infile, outfile, logfile, resolution, dem_dict, ncores=os.cpu_count()):

    '''A wrapper around SNAP's Terrain Correction routine

    This function takes an OST calibrated Sentinel-1 product and
    does the geocodification.

    Args:
        infile: string or os.path object for
                an OST imported frame in BEAM-Dimap format (i.e. *.dim)
        outfile: string or os.path object for the output
                 file written in BEAM-Dimap format
        logfile: string or os.path object for the file
                 where SNAP'S STDOUT/STDERR is written to
        resolution (int): the resolution of the output product in meters
        dem (str): A Snap compliant string for the dem to use.
                   Possible choices are:
                       'SRTM 1sec HGT' (default)
                       'SRTM 3sec'
                       'ASTER 1sec GDEM'
                       'ACE30'
        ncores (int): number of cpus used - useful for parallel processing

    '''

    # get path to SNAP's command line executable gpt
    gpt_file = h.gpt_path()
    
    command = ('{} Terrain-Correction -x -q {}'
            ' -PdemName=\'{}\''
            ' -PdemResamplingMethod=\'{}\''
            ' -PexternalDEMFile=\'{}\''
            ' -PexternalDEMNoDataValue={}'
            ' -PexternalDEMApplyEGM=\'{}\''
            ' -PimgResamplingMethod=\'{}\''
            #' -PmapProjection={}'
            ' -PpixelSpacingInMeter={}'
            ' -t \'{}\' \'{}\''.format(
                    gpt_file, ncores,
                    dem_dict['dem_name'], dem_dict['dem_resampling'],
                    dem_dict['dem_file'], dem_dict['dem_nodata'],
                    str(dem_dict['egm_correction']).lower(),
                    dem_dict['image_resampling'],
                    resolution, outfile, infile
                    )
    )
    
    # run command and get return code
    return_code = h.run_command(command, logfile)

    # handle errors and logs
    if return_code == 0:
        logger.info('Succesfully terrain corrected product')
    else:
        raise GPTRuntimeError(
            'ERROR: Terrain Correction exited with an error {}. See {} for '
            'Snap Error output'.format(return_code, logfile)
        )


@retry(stop_max_attempt_number=3, wait_fixed=1)
def ls_mask(infile, outfile, logfile, resolution, dem_dict, ncores=os.cpu_count()):

    '''A wrapper around SNAP's Layover/Shadow mask routine

    This function takes OST imported Sentinel-1 product and calculates
    the Layover/Shadow mask.

    Args:
        infile: string or os.path object for
                an OST imported frame in BEAM-Dimap format (i.e. *.dim)
        outfile: string or os.path object for the output
                 file written in BEAM-Dimap format
        logfile: string or os.path object for the file
                 where SNAP'S STDOUT/STDERR is written to
        resolution (int): the resolution of the output product in meters
        dem (str): A Snap compliant string for the dem to use.
                   Possible choices are:
                       'SRTM 1sec HGT' (default)
                       'SRTM 3sec'
                       'ASTER 1sec GDEM'
                       'ACE30'
        ncores (int): number of cpus used - useful for parallel processing
    '''

    # get path to SNAP's command line executable gpt
    gpt_file = h.gpt_path()

    # get path to ost package
    rootpath = importlib.util.find_spec('ost').submodule_search_locations[0]

    logger.info('Creating the Layover/Shadow mask')
    # get path to workflow xml
    graph = opj(rootpath, 'graphs', 'S1_GRD2ARD', '3_LSmap.xml')

    # construct command string
#    command = '{} {} -x -q {} -Pinput=\'{}\' -Presol={} -Pdem=\'{}\' \
#             -Poutput=\'{}\''.format(gpt_file, graph, 2 * os.cpu_count(),
#                                     infile, resolution, dem, outfile)
    command = ('{} {} -x -q {} -Pinput=\'{}\' -Presol={} ' 
                                 ' -Pdem=\'{}\'' 
                                 ' -Pdem_file=\'{}\''
                                 ' -Pdem_nodata=\'{}\'' 
                                 ' -Pdem_resampling=\'{}\''
                                 ' -Pimage_resampling=\'{}\''
                                 ' -Pegm_correction=\'{}\''
                                 ' -Poutput=\'{}\''.format(
            gpt_file, graph, ncores, infile, resolution,
            dem_dict['dem_name'], dem_dict['dem_file'], dem_dict['dem nodata'],
            dem_dict['dem_resampling'], dem_dict['image_resampling'],
            str(dem_dict['egm_correction']).lower(), outfile)
    )
    # run command and get return code
    return_code = h.run_command(command, logfile)

    # handle errors and logs
    if return_code == 0:
        logger.info('Succesfully created a Layover/Shadow mask')
    else:
        raise GPTRuntimeError(
            'ERROR: Layover/Shadow mask creation exited with an error {}. '
            'See {} for Snap Error output'.format(return_code, logfile)
        )

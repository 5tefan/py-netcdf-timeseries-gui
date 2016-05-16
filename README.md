# Python NetCDF Time Series Plot GUI

The Python NetCDF Timeseries Plot GUI (pyntpg) is a tool to visualize time
series data originating in NetCDF format. 

## Overview 

The goal of the project is to streamline analysis and visualization of
NetCDF time series data. The program allows you to produce basic time 
series and scatter plots without writing any code. The integrated Ipython
console allows the user to perform any kind of data processing possible
in Python and display the results. 

The software package stands on the shoulders of giants, piecing together:
* PyQt4 Python bindings to the Qt UI library
* netcdf4-python interface to the netCDF C library
* matplotlib python visualization and plotting library
* Jupyter IPython console and kernel
 
The scope of the program is inspired by the Unix philosophy: do one thing
and do it well. While we could work toward an interface reading data from
csv, tsv, etc and plotting line, bar charts, pie charts, etc, we prefer to
instead optimize for the specific use case of time series netcdf data.
Continuing development on the interface is focusing on improving the 
modularity such that adapting to new features may only require rewriting
limited pieces of the interface. The panel_configurer for new plot styles
or the dataset_tabs for reading new data types. 

## Usage

A tutorial workflow is described below 

 1. Open NetCDF files using the "Add Files" button on the dataset tab, or by 
    selecting dataset -> Open files from the menu. Multiple files may be 
    selected which will then be concatenated into one underlying netcdf file
    object. Note that the files must have the same format, otherwise 
    concatenation will fail.
 2. When the import is successful, the progress bar will disappear and an 
    ncinfo like preview of the file will be displayed in the right hand text box.
    At this point, a variable with the same name your dataset tab ("dataset" is
    the default for the first tab) is available in the IPython console, accessible
    from Edit -> Open IPython Console. More datasets can be added by clicking the
    "+" tab, or from File -> New Dataset.
 3. In the plot tab below, customize the panel layout to your preference. We will
    opt for two side by side panels for demonstration. Drag the black bars to the
    nearest edge until the number disappears and you are left with two equally 
    sized panels labeled 0 and 1. 
 4. Below, under "y axis picker", configure the From field to be "dataset", and 
    choose a variable. To make the tutorial simple, hopefully the variable you 
    selected only depends on the time dimension, but if not, options to flatten 
    into a 1 dimensional array should appear. 
 5. Under "x axis picker", select the datetime radio button, then again configure
    the From field to be "dataset", and choose the variable representing time. If
    the units are configured correctly, the date range of your data should display
    in the start and end boxes. You may configure the start and end to constrain
    what is shown.
 6. Stroke color and Stroke style should be ok, feel free to change the color. The
    Stroke style indicators are exactly from matplotlib, '-' is a solid line, '*' 
    makes each point a star, etc. See matplotlib documentation for more. The Panel 
    destination box indicates which panel the data you just configured will be 
    drawn on. You can add the line to panels that are not currently on the layout,
    they will appear if you change their number or add the panel number it is 
    specified on back to they layout. Click "Add to Queue" and the line should 
    appear in the "Queue to plot". You can right click the queued line to change
    color, line style, or the panel it is attached to at any time. 
 7. Next, we will create a scatter plot to add to panel 1 by changing, under "x
    axis picker" the radio button to other. Select another variable to plot 
    a scatter plot against. I suggest selecting line style '.' for scatter plot.
    Select panel destination 1 and Add to Queue. 
 8. Finally, to display the plot, click the green "Create Plot" button at the 
    bottom. A toolbar within the window that should appear allows you to zoom,
    pan, save, and even configure the axes (eg. log, linear, min, max) as well
    as options to change the title and labels.
    
 
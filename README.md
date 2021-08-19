# 3DEP-Farm
# :shark:
> A Python package for retrieving 3DEP's geospatial data and enable users to easily manipulate, transform, subsample and visualize the data. It supports geographic elevation data at the moment and will support more in the future.
<hr>

# Table of Contents
* [Description](#description)
* [Project Structure](#struct)
* [Current Progress](#progress)
* [How to Install](#install)
* [How to Use](#use)
* [References](#refs)
* [License](#license)

# <a name='description'></a>Description
> **LiDAR** (light detection and ranging) is a popular remote sensing mechanism used for measuring the exact distance of an object on the earth's surface. Since the introduction of GPS technology, it has become a widely used method for calculating accurate geospatial measurements. These geospatial data are used for different analysis purposes.
>
>The Purpose of this project is to **help users retrieve these data and enable them to use it easily**, so that they can better understand farmlands and their relations with different factors like elevation, water, soil, and more. 
>
>The Project will make it **easier** for users to access the AWS public dataset with **minimal input** and retrieve the LiDAR results **efficiently**. 

<hr>

# <a name='struct'></a>Project Structure
## Data Source Used:
- https://registry.opendata.aws/usgs-lidar/

<hr>

# <a name='progress'></a>Current Progress
* Main Tasks
  - [x] Enable Elevation Data Fetching
  - [x] Enable Data Loading from saved tif and las/laz files
  - [ ] Enable Terrian Visualization using retrieved or loaded LiDAR cloud points
  - [ ] Enable Cloud Point Standardizing/Sub-Sampling
  - [ ] Enable data augmentation to retrieved geopandas data-frame
  - [ ] Composing a QuickStart Guide Notebook

* Optional Tasks
  - [ ] Enable Diagrammatic way of comparing original terrain and subsampled terrain
  - [ ] Enable Soil-Data Fetching
  - [ ] Enable Climate-Data Fetching
  - [ ] Enable interaction with Sentinel public API
  - [ ] Enable users to download satellite imagery using Sentinels API

<hr>

# <a name='install'></a>How to Install
>Currently the package is not up on PyPi python packages repository. You can download the github repo and use the command:
```
pip install .
```
>When complete the package will be available on PyPi python packages repository. You will be able to install it using the command:
```
pip install 3DEP-Farm
```
<hr>

# <a name='use'></a>How to Use
<hr>

# <a name='refs'></a>References
- https://www.earthdatascience.org/courses/use-data-open-source-python/data-stories/what-is-lidar-data/explore-lidar-point-clouds-plasio/
- https://pdal.io/tutorial/iowa-entwine.html
- https://paulojraposo.github.io/pages/PDAL_tutorial.html
- https://www.earthdatascience.org/courses/use-data-open-source-python/intro-vector-data-python/spatial-data-vector-shapefiles/intro-to-coordinate-reference-systems-python/
- https://towardsdatascience.com/how-to-automate-lidar-point-cloud-processing-with-python-a027454a536c
- https://towardsdatascience.com/farm-design-with-qgis-3fb3ea75bc91
- 
<hr>

# <a name='license'></a>License
[MIT](https://github.com/DePacifier/3DEP-Farm/blob/main/LICENSE)

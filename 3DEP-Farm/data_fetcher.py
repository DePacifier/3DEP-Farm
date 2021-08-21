import logging
from typing import Tuple
import pdal
from json import load, dumps
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.geometry import Point
from logger_creator import CreateLogger
from subsampler import CloudSubSampler


logger = CreateLogger('DataFetcher')
logger = logger.get_default_logger()


class DataFetcher():
    """A Data Fetcher Class which handles all data fetching activites with the AWS dataset 
    and uses all the supporting classes like subsampling.

    Parameters
    ----------
    polygon : Polygon
        Polygon of the area which is being searched for
    epsg : str
        CRS system which the polygon is constructed based on
    region: str, optional
        Region where the specified polygon is located in from the file name folder located in the AWS dataset. If
        not provided the program will search and provide the region if it is in the AWS dataset

    Returns
    -------
    None
    """

    def __init__(self, polygon: Polygon, epsg: str, region: str = '') -> None:
        try:
            self.data_location = "https://s3-us-west-2.amazonaws.com/usgs-lidar-public/"
            minx, miny, maxx, maxy = self.get_polygon_edges(polygon, epsg)

            if(region != ''):
                self.region = self.check_region(region)
                self.file_location = self.data_location + self.region + "/ept.json"
            else:
                self.region = self.get_region_by_bounds(minx, miny, maxx, maxy)
                self.file_location = self.region
            print(self.region)

            self.load_pipeline_template()
            self.epsg = epsg

            logger.info('Successfully Instantiated DataFetcher Class Object')

        except Exception as e:
            logger.exception('Failed to Instantiate DataFetcher Class Object')
            sys.exit(1)

    def check_region(self, region: str) -> str:
        """Checks if a region provided is within the file name folders in the AWS dataset.

        Parameters
        ----------
        region : str
            Proabable file name of a folder in the AWS dataset

        Returns
        -------
        str
            Returns the same regions folder file name if it was successfully located
        """
        with open('./filename.txt', 'r') as locations:
            locations_list = locations.readlines()

        if(region in locations_list):
            return region
        else:
            logger.error('Region Not Available')
            sys.exit(1)

    def get_region_by_bounds(self, minx: float, miny: float, maxx: float, maxy: float, indx: int = 1) -> str:
        """Searchs for a region which satisfies the polygon defined from the available boundaries in the AWS 
        dataset.

        Parameters
        ----------
        minx : float
            Minimum longitude value of the polygon
        miny : float
            Minimum latitude value of the polygon
        maxx : float
            Maximum longitude value of the polygon
        maxy : float
            Maximum latitude value of the polygon
        indx : int, optional
            Bound indexing, to select the first or other access url's of multiple values for a region
        Returns
        -------
        str
            Access url to retrieve the data from the AWS dataset
        """

        aws_dataset_info_csv = pd.read_csv('./aws_dataset.csv')
        for index, bound in enumerate(aws_dataset_info_csv['Bound/s'].to_list()):
            bound = bound.strip('][').replace(
                ']', '').replace('[', '').split(',')
            bound = list(map(float, bound))

            bminx, bminy, bmaxx, bmaxy = bound[0 * indx], bound[1 *
                                                                indx], bound[3 * indx], bound[4 * indx]

            if((minx >= bminx and maxx <= bmaxx) and (miny >= bminy and maxy <= bmaxy)):
                access_url = aws_dataset_info_csv['Access Url/s'].to_list()[
                    index][2:-2]

                region = aws_dataset_info_csv['Region/s'].to_list()[
                    index] + '_' + aws_dataset_info_csv['Year/s'].to_list()[index][2:-2]

                logger.info(f'Region found in {region} folder')

                return access_url
        else:
            logger.error('Region Not Available')
            sys.exit()

    def load_pipeline_template(self, file_name: str = './pipeline_template.json') -> None:
        """Loads Pipeline Template to constructe Pdal Pipelines from.

        Parameters
        ----------
        file_name : str, optional
            Path plus file name of the pipeline template if the template is not located in its normal locations,
            or if another template file is needed to be loaded

        Returns
        -------
        None
        """
        try:
            with open(file_name, 'r') as read_file:
                template = load(read_file)

            self.template_pipeline = template

            logger.info('Successfully Loaded Pdal Pipeline Template')

        except Exception as e:
            logger.exception('Failed to Load Pdal Pipeline Template')
            sys.exit(1)

    def get_polygon_edges(self, polygon: Polygon, epsg: str) -> tuple:
        """To extract polygon bounds and assign polygon cropping bounds.

        Parameters
        ----------
        polygon : Polygon
            Polygon object describing the boundary of the location required
        epsg : str
            CRS system on which the polygon is constructed on

        Returns
        -------
        tuple
            Returns bounds of the polygon provided(minx, miny, maxx, maxy)
        """
        try:
            grid = gpd.GeoDataFrame([polygon], columns=["geometry"])
            grid.set_crs(epsg=epsg, inplace=True)

            grid['geometry'] = grid.geometry.to_crs(epsg=3857)

            minx, miny, maxx, maxy = grid.geometry[0].bounds
            # bounds: ([minx, maxx], [miny, maxy])
            self.extraction_bounds = f"({[minx, maxx]},{[miny,maxy]})"

            # Cropping Bounds
            self.polygon_cropping = self.get_crop_polygon(grid.geometry[0])

            grid['geometry'] = grid.geometry.to_crs(epsg=epsg)
            self.geo_df = grid

            logger.info(
                'Successfully Extracted Polygon Edges and Polygon Cropping Bounds')

            return minx, miny, maxx, maxy

        except Exception as e:
            logger.exception(
                'Failed to Extract Polygon Edges and Polygon Cropping Bounds')

    def get_crop_polygon(self, polygon: Polygon) -> str:
        """Calculates Polygons Cropping string used when building Pdal's crop pipeline.

        Parameters
        ----------
        polygon: Polygon
            Polygon object describing the boundary of the location required

        Returns
        -------
        str
            Cropping string used by Pdal's crop pipeline
        """
        polygon_cords = 'POLYGON(('
        for i in list(polygon.exterior.coords):
            polygon_cords += f'{i[0]} {i[1]},'

        polygon_cords = polygon_cords[:-1] + '))'

        return polygon_cords

    def construct_simple_pipeline(self) -> None:
        """Generates a generic Pdal pipeline.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.pipeline = []
        reader = self.template_pipeline['reader']
        reader['bounds'] = self.extraction_bounds
        reader['filename'] = self.file_location
        self.pipeline.append(reader)

        cropper = self.template_pipeline['cropping_filter']
        cropper['polygon'] = self.polygon_cropping
        self.pipeline.append(cropper)

        self.pipeline.append(self.template_pipeline['range_filter'])
        self.pipeline.append(self.template_pipeline['assign_filter'])

        reprojection = self.template_pipeline['reprojection_filter']
        reprojection['out_srs'] = f"EPSG:{self.epsg}"
        self.pipeline.append(reprojection)

        self.pipeline = pdal.Pipeline(dumps(self.pipeline))

    def construct_pipeline_template_1(self, file_name: str, resolution: int = 1, window_size: int = 6, tif_values: list = ["all"]):
        """Generates a Pdal Pipeline with some configurations available.

        Parameters
        ----------
        file_name : str
            File name used when saving the tiff and LAZ file
        resolution : str
            What resolution to use when generating the tif file
        window_size : int
            Window size to consider when filling empty values to generate the tif file
        tif_values : list
            What values to save in the tif file, like mean, max, min ...

        Returns
        -------
        None
        """
        self.pipeline = []
        reader = self.template_pipeline['reader']
        reader['bounds'] = self.extraction_bounds
        reader['filename'] = self.data_location + self.region + "/ept.json"
        self.pipeline.append(reader)

        self.pipeline.append(self.template_pipeline['range_filter'])
        self.pipeline.append(self.template_pipeline['assign_filter'])

        reprojection = self.template_pipeline['reprojection_filter']
        reprojection['out_srs'] = f"EPSG:{self.epsg}"
        self.pipeline.append(reprojection)

        # Simple Morphological Filter
        self.pipeline.append(self.template_pipeline['smr_filter'])
        self.pipeline.append(self.template_pipeline['smr_range_filter'])

        laz_writer = self.template_pipeline['laz_writer']
        laz_writer['filename'] = f"{file_name}_{self.region}.laz"
        self.pipeline.append(laz_writer)

        tif_writer = self.template_pipeline['tif_writer']
        tif_writer['filename'] = f"{file_name}_{self.region}.tif"
        tif_writer['output_type'] = tif_values
        tif_writer["resolution"] = resolution
        tif_writer["window_size"] = window_size
        self.pipeline.append(tif_writer)

        self.pipeline = pdal.Pipeline(dumps(self.pipeline))

    def get_data(self):
        """Retrieves Data from the AWS Dataset, builds the cloud points from it and 
        assignes and stores the original cloud points and original elevation geopandas dataframe.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        try:
            self.data_count = self.pipeline.execute()
            self.create_cloud_points()
            self.original_cloud_points = self.cloud_points
            self.original_elevation_geodf = self.get_elevation_geodf()
        except Exception as e:
            sys.exit(1)

    def get_pipeline_arrays(self):
        """Returns the Pdal pipelines retrieved data arrays after the pipeline is run.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        return self.pipeline.arrays

    def get_pipeline_metadata(self):
        """Returns the Pdal pipelines metadata of the retrieved data after the pipeline is run.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        return self.pipeline.metadata

    def get_pipeline_log(self):
        """Returns the Pdal pipelines log after the pipeline is run.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        return self.pipeline.log

    def create_cloud_points(self):
        """Creates Cloud Points from the retrieved Pipeline Arrays consisting of other unwanted data.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        try:
            cloud_points = []
            for row in self.get_pipeline_arrays()[0]:
                lst = row.tolist()[-3:]
                cloud_points.append(lst)

            cloud_points = np.array(cloud_points)

            self.cloud_points = cloud_points

        except:
            print('Failed to create cloud points')
            sys.exit(1)

    def get_elevation_geodf(self) -> gpd.GeoDataFrame:
        """Calculates and returns a geopandas elevation dataframe from the cloud points generated before.

        Parameters
        ----------
        None

        Returns
        -------
        gpd.GeoDataFrame
            Geopandas Dataframe with Elevation and coordinate points referenced as Geometry points
        """
        elevation = gpd.GeoDataFrame()
        elevations = []
        points = []
        for row in self.cloud_points:
            elevations.append(row[2])
            point = Point(row[0], row[1])
            points.append(point)

        elevation['elevation'] = elevations
        elevation['geometry'] = points
        elevation.set_crs(epsg=self.epsg, inplace=True)

        self.elevation_geodf = elevation

        return self.elevation_geodf

    def get_scatter_plot(self, factor_value: int = 1, view_angle: Tuple[int, int] = (0, 0)) -> plt:
        """Constructs a scatter plot graph of the cloud points.

        Parameters
        ----------
        factor_value : int, optional
            Factoring value if the data points are huge
        view_angle : tuple(int, int), optional
            Values to change the view angle of the 3D projection

        Returns
        -------
        plt
            Returns a scatter plot grpah of the cloud points
        """

        values = self.cloud_points[::factor_value]

        fig = plt.figure(figsize=(10, 15))

        ax = plt.axes(projection='3d')

        ax.scatter3D(values[:, 0], values[:, 1],
                     values[:, 2], c=values[:, 2], s=0.1, cmap='terrain')

        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_zlabel('Elevation')

        ax.set_title('Elevation Scatter Plot')

        ax.view_init(view_angle[0], view_angle[1])

        return plt

    def get_terrain_map(self, markersize: int = 10, fig_size: Tuple[int, int] = (15, 20)) -> plt:
        """Constructs a Terrain Map from the cloud points.

        Parameters
        ----------
        markersize : int, optional
            Marker size used when ploting the figure
        fig_size : Tuple[int, int], optional
            Size of the figure to be returned

        Returns
        -------
        plt
            Returns a Terrain Map constructed from the cloud points
        """
        self.get_elevation_geodf()

        self.elevation_geodf.plot(c='elevation', scheme="quantiles", cmap='terrain', legend=True,
                                  markersize=markersize,
                                  figsize=(fig_size[0], fig_size[1]),
                                  missing_kwds={
                                    "color": "lightgrey",
                                    "edgecolor": "red",
                                    "hatch": "///",
                                    "label": "Missing values"}
                                  )

        plt.title('Terrain Elevation Map')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')

        return plt

    # def compare_original_sampled_scatter_plot(self):
    #     pass

    def apply_factor_sampling(self, factor: int):
        """Apply Factor Sampling on the Cloud Points.

        Parameters
        ----------
        factor : int
            Steps to take to select the next sample from the Cloud Points.           

        Returns
        -------
        None
        """
        self.sampler_class = CloudSubSampler(self.cloud_points)
        self.cloud_points = self.sampler_class.get_factor_subsampling(
            factor=factor)

    def apply_grid_sampling(self, voxel_size: float, sampling_type: str = 'closest'):
        """Apply Grid Sampling on the Cloud Points.

        Parameters
        ----------
        voxel_size : float
            Size of the voxel to consider when applying the grid sampling
        sampling_type : str, optional
            Type of sampling to be used when applying the grid sampling

        Returns
        -------
        None
        """
        self.sampler_class = CloudSubSampler(self.cloud_points)
        self.cloud_points = self.sampler_class.get_grid_subsampling(
            voxel_size=voxel_size, sampling_type=sampling_type)

    def save_cloud_points_for_3d(self, filename: str):
        """Save the variable to an ASCII file to open in a 3D Software.

        Parameters
        ----------
        file_name : str
            String of the path plus name to save the cloud point on to

        Returns
        -------
        None
        """
        np.savetxt(filename + "_cloud_points.xyz",
                   self.cloud_points, delimiter=";", fmt="%s")


if __name__ == "__main__":
    MINX, MINY, MAXX, MAXY = [-93.756155, 41.918015, -93.747334, 41.921429]
    polygon = Polygon(((MINX, MINY), (MINX, MAXY),
                       (MAXX, MAXY), (MAXX, MINY), (MINX, MINY)))

    df = DataFetcher(polygon=polygon, region="IA_FullState", epsg="4326")

    df.construct_simple_pipeline()

    df.get_data()

    elevation = df.elevation_geodf()

    elevation.sample(10)

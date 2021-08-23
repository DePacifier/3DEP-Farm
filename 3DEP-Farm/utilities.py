from logging import log
from urllib.request import urlopen
from json import dump, loads
from time import sleep
import pandas as pd
import sys
from copy import copy
from logger_creator import CreateLogger

logger = CreateLogger('Utilities')
logger = logger.get_default_logger()


def get_info(url_str: str) -> tuple:
    """Retrieve ept.json information from the AWS storage using python urlopen request

    Parameters
    ----------
    url_str : str
        URL to the ept.json file.

    Returns
    -------
    tuple
        A tuple with bounds, numbers of points, reprojection and schema information extracted from the ept.json file.
    """
    try:
        # store the response of URL
        response = urlopen(url_str)
        # storing the JSON response
        # read data from response
        data_json = loads(response.read())

        return_data = data_json['bounds'], data_json['points']

        logger.info(
            'Successfully Read and Retrieved Data Information from EPT.JSON File')

        # return extracted values
        return return_data

    except Exception as e:
        logger.exception('Failed To Read EPT.JSON File From URL')
        sys.exit(1)


def construct_aws_dataset_json(directories_path: str = './filename.txt', save: bool = False) -> dict:
    """Construct AWS Dataset Data Information. It extracts and identifies similar locations and organize them
    properly. It can also save the generated JSON file if needed.

    Parameters
    ----------
    directories_path : str, optional
        Path plus filename of the text file which contains the names of folders which are located in the AWS dataset storage.
        If filename of the directories is not given providing the file location is a must.
    save: bool, optional
        To save the generated json file in the same directory where the function was called.
    Returns
    -------
    dict
        The generated AWS Data Information in a json/dictionary format.
    """

    main_url = "https://usgs-lidar-public.s3.us-west-2.amazonaws.com/"

    dataset_json = {}

    with open('./filename.txt', 'r') as locations:
        locations_list = locations.readlines()

    for index, location in enumerate(locations_list):
        try:
            location = location.replace('\n', "")[:-1]
            folder_url = main_url + location + '/ept.json'
            bound, points, reprojection, schema = get_info(folder_url)
            location = location.split('_')
            if('LAS' in location and location[location.index('LAS') - 1].isnumeric()):
                file_name = '_'.join(location[:-3])
                year = location[-3] + '-' + location[-1]
            else:
                file_name = '_'.join(location[:-1])
                year = location[-1]

            if(file_name not in dataset_json.keys()):
                new_file = {}
                new_file['bounds'] = [bound]
                new_file['years'] = [year]
                new_file['points'] = [points]
                new_file['access_url'] = [folder_url]
                new_file['len'] = 1
                dataset_json[file_name] = new_file

            else:
                dict_value = dataset_json[file_name]
                dict_value['bounds'].append(bound)
                dict_value['years'].append(year)
                dict_value['points'] = [points]
                dict_value['access_url'].append(folder_url)
                dict_value['len'] = dict_value['len'] + 1

                dataset_json.update({file_name: dict_value})

            print(index, end=', ')
            if(index % 100 == 0):
                sleep(5)

        except Exception as e:
            logger.info('Failed To retrieve:\n\tfile_index -> ', index)
            logger.info("Reason:\n\t -> ", e)
            continue

    if(save):
        with open('./aws_dataset_info.json', 'w') as file_handler:
            dump(dataset_json, file_handler, sort_keys=True, indent=4)

    logger.info('Successfully generated Data Information JSON File')

    return dataset_json


def get_values_list(json_data: dict) -> tuple:
    """Deconstructs the given dictionary values into specific data information values within the dictionary.

    Parameters
    ----------
    json_data : dict
        Dictionary data from which the data informations are extracted from.

    Returns
    -------
    tuple
        Tuple of lists for each extracted informations.
    """
    try:
        file_names = list(json_data.keys())
        bounds_list = []
        points_list = []
        years_list = []
        access_list = []
        len_list = []
        for value in json_data.values():
            bounds_list.append(value['bounds'])
            points_list.append(value['points'])
            years_list.append(value['years'])
            access_list.append(value['access_url'])
            len_list.append(value['len'])

        return_value = (file_names, bounds_list, points_list,
                        years_list, access_list, len_list)

        logger.info('Successfully Retrieved Value Lists')

    except Exception as e:
        logger.exception('Failed to Retrieve Value Lists')

    return return_value


def merge_similar_bounds(json_data: dict, file_names: list, bounds_list: list) -> dict:
    """Finds keys in a dictionary where there bounds are similar and merges them.

    Parameters
    ----------
    json_data : dict
        Dictionary data from which the data informations were extracted from.
    file_names : list
        Keys list extracted from the Dictionary
    bounds_list : list
        Bounds list extracted from the Dictionary

    Returns
    -------
    dict
        New Dictionary where files with similar bounds are merged together.
    """
    try:
        new_json = copy.deepcopy(json_data)

        check = []
        similar_values = []

        for index, i in enumerate(bounds_list):
            if i in check:
                similar_values.append([check.index(i), index])
                print("actual first index:", check.index(
                    i), "bound index value:", index)
            else:
                check.append(i)

        for initial, later in similar_values:
            main_json = new_json[file_names[initial]]
            add_json = new_json[file_names[later]]

            new_file_name = f'{file_names[initial]},{file_names[later]}'
            new_file = {}
            new_file['bounds'] = main_json['bounds']
            new_file['years'] = main_json['years']
            new_file['years'].extend(add_json['years'])
            new_file['points'] = main_json['points']
            new_file['points'].extend(add_json['points'])
            new_file['access_url'] = main_json['access_url']
            new_file['access_url'].extend(add_json['access_url'])
            new_file['len'] = main_json['len'] + add_json['len']

            del new_json[file_names[initial]]
            del new_json[file_names[later]]

            new_json[new_file_name] = new_file

        logger.info('Successfully merged files with related bounds')

    except Exception as e:
        logger.exception('Failed to merge bound related files')

    return new_json


def fix_bound_reptition_and_build_csv(json_data: dict, save: bool = True) -> pd.DataFrame:
    """Fixes bound repition problems in a json files and builds a CSV representation of the JSON file.

    Parameters
    ----------
    json_data : dict
        Dictionary from which the CSV is built.
    save : bool, optional
        To save the generated CSV file with the name aws_dataset.csv in the current call path or not.

    Returns
    -------
    pd.DataFrame
        Pandas DataFrame representation of the JSON file with all bound similarities merged.
    """
    file_names, bounds_list, points_list, reprojection_list, schema_list, years_list, access_list, len_list = get_values_list(
        json_data)

    final_json = merge_similar_bounds(json_data, file_names, bounds_list)

    file_names, bounds_list, points_list, years_list, access_list, len_list = get_values_list(
        final_json)

    aws_dataset_df = pd.DataFrame()
    aws_dataset_df['Region/s'] = file_names
    aws_dataset_df['Bound/s'] = bounds_list
    aws_dataset_df['NumberOfPoints'] = points_list
    aws_dataset_df['Year/s'] = years_list
    aws_dataset_df['Access Url/s'] = access_list
    aws_dataset_df['Variations'] = len_list

    if(save):
        aws_dataset_df.to_csv('./aws_dataset.csv')

    logger.info(
        'Successfully Generated CSV file from JSON file applying bound merge fixes')

    return aws_dataset_df


if __name__ == "__main__":
    final = construct_aws_dataset_json()
    df = fix_bound_reptition_and_build_csv(final, save=False)

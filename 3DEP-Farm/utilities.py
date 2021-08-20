from urllib.request import urlopen
from json import dump, loads
from time import sleep
import pandas as pd
from copy import copy


def get_bounds(url_str: str) -> list:
    # store the response of URL
    response = urlopen(url_str)
    # storing the JSON response
    # from url in data
    data_json = loads(response.read())
    # print the json response
    return data_json['bounds']


def construct_aws_dataset_json(directories_path: str = './filename.txt', save: bool = False):

    main_url = "https://usgs-lidar-public.s3.us-west-2.amazonaws.com/"

    dataset_json = {}

    with open('./filename.txt', 'r') as locations:
        locations_list = locations.readlines()

    for index, location in enumerate(locations_list):
        try:
            location = location.replace('\n', "")[:-1]
            folder_url = main_url + location + '/ept.json'
            bound = get_bounds(folder_url)
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
                new_file['access_url'] = [folder_url]
                new_file['len'] = 1
                dataset_json[file_name] = new_file

            else:
                dict_value = dataset_json[file_name]
                dict_value['bounds'].append(bound)
                dict_value['years'].append(year)
                dict_value['access_url'].append(folder_url)
                dict_value['len'] = dict_value['len'] + 1

                dataset_json.update({file_name: dict_value})

            print(index, end=', ')
            if(index % 100 == 0):
                sleep(5)

        except Exception as e:
            print('Failed: ', index)
            print("Reason: ", e)
            continue

    if(save):
        with open('./aws_dataset_info.json', 'w') as file_handler:
            dump(dataset_json, file_handler, sort_keys=True, indent=4)

    return dataset_json


def get_values_list(json_data: dict):
    file_names = list(json_data.keys())
    bounds_list = []
    years_list = []
    access_list = []
    len_list = []
    for value in json_data.values():
        bounds_list.append(value['bounds'])
        years_list.append(value['years'])
        access_list.append(value['access_url'])
        len_list.append(value['len'])

    return file_names, bounds_list, years_list, access_list, len_list


def merge_similar_bounds(json_data: dict, file_names: list, bounds_list: list):
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
        new_file['access_url'] = main_json['access_url']
        new_file['access_url'].extend(add_json['access_url'])
        new_file['len'] = main_json['len'] + add_json['len']

        del new_json[file_names[initial]]
        del new_json[file_names[later]]

        new_json[new_file_name] = new_file

    return new_json


def fix_bound_reptition_and_build_csv(json_data: dict, save: bool = True):
    file_names, bounds_list, years_list, access_list, len_list = get_values_list(
        json_data)

    final_json = merge_similar_bounds(json_data, file_names, bounds_list)

    file_names, bounds_list, years_list, access_list, len_list = get_values_list(
        final_json)

    aws_dataset_df = pd.DataFrame()
    aws_dataset_df['Region/s'] = file_names
    aws_dataset_df['Bound/s'] = bounds_list
    aws_dataset_df['Year/s'] = years_list
    aws_dataset_df['Access Url/s'] = access_list
    aws_dataset_df['Variations'] = len_list

    if(save):
        aws_dataset_df.to_csv('./aws_dataset.csv')

    return aws_dataset_df


if __name__ == "__main__":
    final = construct_aws_dataset_json()
    df = fix_bound_reptition_and_build_csv(final, save=False)

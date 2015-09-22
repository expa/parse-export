#!/usr/bin/env python2.7

import argparse
import contextlib
import httplib
import json
import os
import pytz
import shutil
import sys
import tarfile
import tempfile
import time
import traceback
import urllib

from datetime import datetime

TEMP_DIRECTORY = tempfile.mkdtemp(prefix='/tmp/parse-export-')


def get_env_setting(setting):
    """ Get the environment setting or return exception """
    try:
        return os.environ[setting]
    except KeyError, e:
        error_msg = 'Set the %s env variable' % setting
        print error_msg
        raise e


@contextlib.contextmanager
def change_dir(tmp_location):
    cd = os.getcwd()
    os.chdir(tmp_location)
    try:
        yield
    finally:
        os.chdir(cd)


def get_parse_data(connection, app_id, rest_api_key, api_endpoint, master_key=None, limit=1000, order=None, skip=None, filter_json=None, api_version=1):
    try:
        connection.connect()
    except Exception, e:
        print(traceback.format_exc())
        raise ParseExportException(e)

    header_dict = {'X-Parse-Application-Id': app_id,
                   'X-Parse-REST-API-Key': rest_api_key
                   }

    if master_key is not None:
        header_dict['X-Parse-Master-Key'] = master_key

    params_dict = {}
    if order is not None:
        params_dict['order'] = order
    if limit is not None:
        params_dict['limit'] = limit
    if skip is not None:
        params_dict['skip'] = skip
    if filter_json is not None:
        params_dict['where'] = filter_json

    params = urllib.urlencode(params_dict)
    connection.request('GET', '/%s/%s?%s' % (api_version, api_endpoint, params), '', header_dict)

    try:
        response = json.loads(connection.getresponse().read())
    except Exception, e:
        response = None
        print(traceback.format_exc())
        raise e

    return response

# parse command-line args
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--archive-file', dest='archive_file_path', required=True, help='output archive file path (tar.bz2)')
parser.add_argument('-o', '--export-objects', dest='parse_export_list', required=True, help='comma-separated list of parse objects to export')
parser.add_argument('--parse-app-id', dest='parse_app_id', help='parse app id (or export PARSE_APPLICATION_ID)')
parser.add_argument('--parse-api-key', dest='parse_api_key', help='parse api key (or export PARSE_REST_API_KEY)')
parser.add_argument('--parse-master-key', dest='parse_master_key', help='parse master key (or export PARSE_MASTER_KEY)')
args = parser.parse_args()


def cleanup(temp_directory=TEMP_DIRECTORY):
    print 'cleaning up: %s' % (temp_directory)
    try:
        shutil.rmtree(temp_directory)
    except OSError:
        pass
    except Exception, e:
        print(traceback.format_exc())
        raise e


class ParseExportException(Exception):
    def __init__(self, message):
        super(ParseExportException, self).__init__(message)

        cleanup()


def main(temp_directory=TEMP_DIRECTORY, archive_file_path=args.archive_file_path):
    print '---- beginning parse object dump: %s ----' % datetime.strftime(datetime.now(pytz.utc), '%Y-%m-%d %H:%M:%S %z')

    PARSE_APPLICATION_ID = get_env_setting('PARSE_APPLICATION_ID') or args.parse_app_id
    PARSE_REST_API_KEY = get_env_setting('PARSE_REST_API_KEY') or args.parse_api_key
    PARSE_MASTER_KEY = get_env_setting('PARSE_MASTER_KEY') or args.parse_master_key
    INTERNAL_PARSE_CLASSES = {'User': 'users', 'Role': 'roles', 'File': 'files', 'Events': 'events', 'Installation': 'installations'}

    parse_export_list = args.parse_export_list.split(",")

    for classname in parse_export_list:
        connection = httplib.HTTPSConnection('api.parse.com', 443)

        get_parse_data_startime = time.time()
        parse_request_count = 0

        results = {'results': []}
        object_count = 0
        startdate = '2000-01-01T00:00:00.000Z'

        if classname not in INTERNAL_PARSE_CLASSES.keys():
            endpoint = '%s/%s' % ('classes', classname)
        else:
            endpoint = INTERNAL_PARSE_CLASSES[classname]

        sys.stdout.write('retrieving %s objects... \n' % classname)
        sys.stdout.flush()

        while True:
            parse_filter = json.dumps({'createdAt': {'$gte': {'__type': 'Date', 'iso': startdate}}})
            parse_response = get_parse_data(connection, PARSE_APPLICATION_ID, PARSE_REST_API_KEY, endpoint, master_key=PARSE_MASTER_KEY, order='createdAt', filter_json=parse_filter)
            parse_request_count += 1
            intermediate_get_parse_data_time = time.time() - get_parse_data_startime

            sys.stdout.write('  retrieved %d objects with %d reqs for %s in %.4f seconds \r' % (object_count, parse_request_count, classname, intermediate_get_parse_data_time))
            sys.stdout.flush()

            if 'results' in parse_response.keys() and len(parse_response['results']) > 1:
                # print '%s: %d, %s' % (classname, len(parse_response['results']), parse_response['results'][-1]['createdAt'])
                startdate = parse_response['results'][-1]['createdAt']
                object_count += len(parse_response['results'])
                results['results'].extend(parse_response['results'])
            else:
                break

        with open(os.path.join(temp_directory, '%s.json' % classname), 'w') as json_file:
            json_file.write(json.dumps(results, indent=4, separators=(',', ': ')))

        parse_roundtrip_seconds = time.time() - get_parse_data_startime

        sys.stdout.write('  retrieved %d objects with %d reqs for %s in %.4f seconds \n' % (object_count, parse_request_count, classname, parse_roundtrip_seconds))
        sys.stdout.flush()

    sys.stdout.write('building archive... ')
    sys.stdout.flush()

    build_archive_starttime = time.time()

    with tarfile.open(name=archive_file_path, mode='w:bz2') as tar:
        with change_dir(temp_directory):
            for f in os.listdir('.'):
                tar.add(f)
    sys.stdout.write(' done. (in %.4f seconds)\n' % (time.time() - build_archive_starttime))
    sys.stdout.flush()

    cleanup(temp_directory)

    sys.stdout.write('---- completed parse object dump: %s ----\n' % datetime.strftime(datetime.now(pytz.utc), '%Y-%m-%d %H:%M:%S %z'))
    sys.stdout.flush()

if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        print(traceback.format_exc())
        raise ParseExportException(e)

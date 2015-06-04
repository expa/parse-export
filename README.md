# Parse Export [![Build Status](https://img.shields.io/circleci/project/expa/parse-export.svg "Build Status")](https://circleci.com/gh/expa/parse-export/tree/master)

Simple python script to export [Parse](http://parse.com/) data

## Requirements

    pip -r requirements.txt

## Usage
```
usage: parse_export.py [-h] -f ARCHIVE_FILE_PATH -o PARSE_EXPORT_LIST
                       [--parse-app-id PARSE_APP_ID]
                       [--parse-api-key PARSE_API_KEY]
                       [--parse-master-key PARSE_MASTER_KEY]

optional arguments:
  -h, --help            show this help message and exit
  -f ARCHIVE_FILE_PATH, --archive-file ARCHIVE_FILE_PATH
                        output archive file path (tar.bz2)
  -o PARSE_EXPORT_LIST, --export-objects PARSE_EXPORT_LIST
                        comma-separated list of parse objects to export
  --parse-app-id PARSE_APP_ID
                        parse app id
  --parse-api-key PARSE_API_KEY
                        parse api key
  --parse-master-key PARSE_MASTER_KEY
                        parse master key
```

## Contributing

Feel free to fork and create a Pull Request. (Please add your name to AUTHORS)

## License

MIT

import json
import os

for filename in os.listdir(os.getcwd()):
    if filename.endswith('.json'):
        print "attempting to validate: %s" % filename
        with open(filename) as json_file:
            try:
                json.load(json_file)
            except Exception, err:
                print 'invalid json in %s: %s' % (filename, err)

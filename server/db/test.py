#!/Users/jamieinfinity/anaconda/envs/py27/bin/python

import myfitnesspal

client = myfitnesspal.Client('jamieinfinity')

data = client.get_date(2017, 8, 30)

f1=open('/Users/jamieinfinity/Projects/WorldLine/worldline-wgt/server/db/testoutput.dat', 'w+')
f1.write(str(data))
f1.close()

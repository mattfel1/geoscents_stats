import csv, json, sys
import numpy as np

# We no longer generate csvs, so this script isn't used anywhere

#if you are not using utf-8 files, remove the next line
#sys.setdefaultencoding("UTF-8") #set the encode to utf8
#check if you pass the input file and output file
if sys.argv[1] is not None and sys.argv[2] is not None:
    fileInput = sys.argv[1]
    fileOutput = sys.argv[2]
    inputFile = open(fileInput) #open json file
    outputFile = open(fileOutput, 'w') #load csv file
    data = json.load(inputFile) #load json content
    inputFile.close() #close the input file
    output = csv.writer(outputFile) #create a csv.write
    longest = 0
    for row in data.keys():
        if (len(data[row]['dists']) > longest): longest = len(data[row]['dists'])
    print(longest)
    header = ['citystring', 'mean_dist', 'std_dist', 'mean_time', 'std_time', 'num_guesses'] + ['dists%d' % i for i in range(longest)] + ['times%d' % i for i in range(longest)] + ['region%d' % i for i in range(longest)] + ['country%d' % i for i in range(longest)]
    outputFile.write('\t'.join(header) + '\n')
    for row in data.keys():
        #print(data[row])
        l = data[row]
        try:
            dists = ['' if (i >= len(l['dists'])) else str(x) for i,x in enumerate(l['dists'])]
            times = ['' if (i >= len(l['times'])) else str(x) for i,x in enumerate(l['times'])]
            regions = ['' if (i >= len(l['regions'])) else str(x) for i,x in enumerate(l['regions'])]
            countries = ['' if (i >= len(l['countries'])) else str(x) for i,x in enumerate(l['countries'])]
            st = '%s\t%s\t%s\t%s\t%s\t%d\t' % (row, l['mean_dist'], l['std_dist'], l['mean_time'], l['std_time'], len(l['dists'])) + ('\t'.join(dists)) + ('\t'.join(times)) + ('\t'.join(regions)) + ('\t'.join(countries))
            outputFile.write(st + '\n') #values row
        except:
            print('Error on %s' % row)

    outputFile.close()

    import sys
    import csv
    
    lines = csv.reader(open(fileOutput), delimiter="\t")
    reader = []
    for r in lines:
        reader.append(r)
    header = reader.pop(0)
    def toFlt(x):
        try: 
            return float(x)
        except:
            return -1.0
    sortedlist = sorted(reader, key=lambda row: toFlt(row[1]), reverse=True)
    output = open(fileOutput, 'w')
    output.write('\t'.join(header) + '\n')
    for row in sortedlist:
        output.write('\t'.join(row) + '\n')
    output.close()

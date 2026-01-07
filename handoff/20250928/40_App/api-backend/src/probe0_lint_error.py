import os, sys
def get_files(path):
  try:
    for file in os.listdir(path)
      print file
  except:
    print "An error occurred"

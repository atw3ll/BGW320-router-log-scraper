#!/usr/bin/env python3

import pycurl
import argparse
import signal
import json
import threading
from io import BytesIO
from io import StringIO
from html.parser import HTMLParser
from time import sleep
from os import environ

arg = argparse.ArgumentParser(
        prog='atnt_forward.py',
        usage='atnt_forward.py [options]',
        conflict_handler='resolve',
        description='Downloads logs from AT&T ISP router, checks for new entries, and then forwards them over raw tcp socket.',
        epilog='Have Fun'
        )

arg.add_argument('-DEBUG', '-d', '--debug', action='store_true', help='Enable Debugging')
arg.add_argument('-IP', '-i', '--ip', type=str, help='Set IP address to scrape')
arg.add_argument('-TIME', '-T', '--time', type=int, help='Set Query Interval Seconds')
arg.add_argument('-CACHEFILE', '-F', '--file', type=str, help='Cache File Location')
cmdArgs = arg.parse_args()

interval = 12 if cmdArgs.time == None else cmdArgs.time

if cmdArgs.file != None and os.path.isfile(cmdArgs.file):
    location = cmdArgs.file
else:
    location = f"{environ['HOME']}/.cache/routerData/lastRouterSave.txt"

class routerHTMLParser(HTMLParser):
    # No. Time Src IP Dst IP Proto Reason
    tempList   = []
    organized  = dict()
    tBodyFound = False
    inRow      = False
    rowCount   = -1
    def handle_starttag(self, tag, attrs):
        if self.tBodyFound and tag == 'tr':
            self.inRow = True
            self.rowCount += 1
        elif tag == 'tbody':
            self.tBodyFound = True
    def handle_endtag(self, tag):
        if self.tBodyFound and tag == 'tr':
            self.inRow = False
            if not self.tempList:
                pass
            else:
                self.organized[self.tempList[1]] = self.tempList.copy()
                self.tempList.clear()
        elif tag == 'tbody':
            self.tBodyFound = False
    def handle_data(self, data):
        if self.inRow and self.tBodyFound:
            if data.find("repeated") != -1:
                pass
                # print("REPEATED:" + data )
            else:
                self.tempList.append(data)

class routerHTMLParserDEBUG(HTMLParser):
    tempList   = []
    organized  = dict()
    tBodyFound = False
    inRow      = False
    rowCount   = -1
    def handle_starttag(self, tag, attrs):
        print("Start tag:", tag)
        if self.tBodyFound and tag == 'tr':
            self.inRow = True
            self.rowCount += 1
        elif tag == 'tbody':
            self.tBodyFound = True
        # routerHTMLParser().handle_starttag(tag, attrs)
    def handle_endtag(self, tag):
        print("End tag  :", tag)
        if self.tBodyFound and tag == 'tr':
            self.inRow = False
            if not self.tempList:
                pass
            else:
                self.organized[self.tempList[1]] = self.tempList.copy()
                self.tempList.clear()
        elif tag == 'tbody':
            self.tBodyFound = False
        # routerHTMLParser().handle_endtag(tag)
    def handle_data(self, data):
        print("Data     :", data)
        if self.inRow and self.tBodyFound:
            if data.find("repeated") != -1:
                print("REPEATED:" + data )
                pass
            else:
                self.tempList.append(data)
        # routerHTMLParser().handle_data(data)

def sendData(extracted_data):
    print(extracted_data)
    curl = pycurl.Curl()
    curl.setopt(curl.URL, "http://0.0.0.0:5555/raw")
    curl.setopt(curl.READDATA, StringIO(extracted_data))
    curl.setopt(curl.POST, 1)
    curl.setopt(curl.VERBOSE, True)
    curl.perform()
    curl.close()

def newData():
    buffer = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.URL, f"http://{cmdArgs.ip}/cgi-bin/logs.ha")
    curl.setopt(curl.WRITEDATA, buffer)
    curl.perform()
    curl.close()
    html = routerHTMLParserDEBUG() if cmdArgs.debug else routerHTMLParser()
    html.feed(' '.join(buffer.getvalue().decode('utf-8').split()))
    return html.organized.copy()

class GracefulKiller:
  kill_now = False
  sleeper_thread = None
  test_event = None
  def __init__(self):
    signal.signal(signal.SIGINT,  self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)
  def exit_gracefully(self, signum, frame):
    self.kill_now = True
    # print(sleeper_thread)
    if self.sleeper_thread is not None:
        # print("CHEEEEEESE")
        self.test_event.set()
  def sleeping_function(self, time):
    self.test_event.wait(timeout = time)
  def timer_wait(self, time):
    self.test_event = threading.Event()
    self.sleeper_thread = threading.Thread(target=self.sleeping_function, args=([time]))
    self.sleeper_thread.start()
    self.sleeper_thread.join()

processAssassin = GracefulKiller()

che = newData() 
cutOffPoint      = tuple(che.keys())[0]
sliced_keys_list = tuple(che.keys())[0:len(che) - 1]

while not processAssassin.kill_now:
    for k in sliced_keys_list:
        # No. Time Src IP Dst IP Proto Reason
        # print(json.dumps(
        sendData(json.dumps(
            {
            "Time"        : che[k][1],
            "Source"      : che[k][2],
            "Destination" : che[k][3],
            "Protocol"    : che[k][4],
            "Reason"      : che[k][5]
            }
            ))
    cutOffPoint = sliced_keys_list[len(sliced_keys_list) - 1]
    che.clear()
    che = newData()
    sliced_keys_list = tuple(che.keys())[list(che.keys()).index(cutOffPoint):len(che) - 1]
    # sleep(interval)
    processAssassin.timer_wait(interval)

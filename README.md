Created for the purpose of forwarding logs from BGW320-500 AT&T routers to raw tcp socket for log management.

![Alt text](image.png)

### Setting up the environment
```
git clone https://github.com/atw3ll/ISP-router-log-scraper.git
cd ISP-router-log-scraper
python3 -m venv .
source bin/activate
chmod +x atnt_forward.py
./atnt_forward.py
```

### Help page
```
usage: atnt_forward.py [options]

Downloads logs from AT&T ISP router, checks for new entries, and then forwards them over raw tcp socket.

options:
  -h, --help            show this help message and exit
  -DEBUG, -d, --debug   Enable Debugging
  -IP, -i, --ip IP      Set IP address to scrape
  -TIME, -T, --time TIME
                        Set Query Interval Seconds
  -CACHEFILE, -F, --file FILE
                        Cache File Location
```

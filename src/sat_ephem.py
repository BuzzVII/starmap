import requests
import pickle
import concurrent.futures

URL = 'https://celestrak.com/satcat/tle.php?CATNR='
START_TLE = 44235
END_TLE = 45787

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def download_tle(i):
    tle = None
    res = requests.get(f'{URL}{i}')
    if res.ok:
        tle = res.content
    # Press Ctrl+F8 to toggle the breakpoint.
    return tle


# Press th green button in the gutter to run the script.
if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor() as eggcecutor:
        futures = [eggcecutor.submit(download_tle, (i,)) for i in range(START_TLE, END_TLE+1)]
    sats = [f.result() for f in futures]
    with open('starlink_tle.pickle', 'wb') as fp:
        pickle.dump(sats, fp)

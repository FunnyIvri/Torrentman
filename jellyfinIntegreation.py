from json import dump, loads
from pathlib import Path
from threading import Thread
from time import sleep

from requests import get, post
from constants import JELLYFIN_API_URL, JELLYFIN_AUTH_HEADER

def getLibrarys():
    print(JELLYFIN_API_URL + "/Library/VirtualFolders")
    res = get(JELLYFIN_API_URL + "/Library/VirtualFolders",headers=JELLYFIN_AUTH_HEADER)
    print(res)
    return loads(res.text)
def getContent(libaryId : str):
    res = get(JELLYFIN_API_URL + "/Items", headers=JELLYFIN_AUTH_HEADER,params={
        "startIndex" : 0,
        "limit": 999,
        "recursive": True,
        "sortOrder":"Ascending",
        "parentId": libaryId,
        "fields": [
            "MediaSourceCount",
            "PrimaryImageAspectRatio"
        ],
        "sortBy": "SortName",
    })
    print(res)
    return loads(res.text)
def triggerRefresh():
    res = post(JELLYFIN_API_URL + "/Library/Refresh")
    
    # reload local libary to be up to date on jellyfin libary when the refresh is complete
    Thread(target=recheckLibaryOnRefreshComplete).start() 
    
    return res
def checkForRefreshComplete():
    try:
        res = get(JELLYFIN_API_URL + "/ScheduledTasks?isHidden=false")
        data = loads(res.text)
        for task in data:
            if task["Name"] == "Scan Media Library":
                if  task["State"] == "Idle":
                    return True
                else: return False
    except:pass
    return False
def recheckLibaryOnRefreshComplete():
    while True:
        if checkForRefreshComplete():
            triggerRefresh()
            return  # Ends the thread
        else: sleep(1)
TV_SHOWS_FOLDER = Path("")
MOVIES_FOLDER = Path("")
TV_SHOWS_LIBRARY_ID = ""
MOVIES_LIBRARY_ID = ""

TV_SHOWS = {}
MOVIES = []
def loadMoviesAndShows():
    global TV_SHOWS_FOLDER,MOVIES_FOLDER,TV_SHOWS_LIBRARY_ID,MOVIES_LIBRARY_ID
    for library in getLibrarys():
        if TV_SHOWS_FOLDER != Path("") and MOVIES_FOLDER != Path(""):
            break
        if library["CollectionType"] == "tvshows":
            TV_SHOWS_FOLDER = Path(library["Locations"][0])
            TV_SHOWS_LIBRARY_ID = library["ItemId"]
        elif library["CollectionType"] == "movies":
            MOVIES_FOLDER = Path(library["Locations"][0])
            MOVIES_LIBRARY_ID = library["ItemId"]
    for content in getContent(TV_SHOWS_LIBRARY_ID)["Items"]:
        match (content["Type"].lower()):
           case "episode":
               if not TV_SHOWS.get(content["SeriesName"]):
                   TV_SHOWS[content["SeriesName"]] = {}
               if not TV_SHOWS[content["SeriesName"]].get(
                   str(content["ParentIndexNumber"])
               ):
                   TV_SHOWS[content["SeriesName"]][str(content["ParentIndexNumber"])] = {}
               TV_SHOWS[content["SeriesName"]][str(content["ParentIndexNumber"])][
                   str(content["IndexNumber"])
               ] = content["Name"]
           case "season":
               if not TV_SHOWS.get(content["SeriesName"]):
                   TV_SHOWS[content["SeriesName"]] = {}
               if not TV_SHOWS[content["SeriesName"]].get(str(content["IndexNumber"])):
                   TV_SHOWS[content["SeriesName"]][str(content["IndexNumber"])] = {}
           case "series":
               if not TV_SHOWS.get(content["Name"]):
                   TV_SHOWS[content["Name"]] = {}
    for content in getContent(MOVIES_LIBRARY_ID)["Items"]:
        if content["Type"] == "Folder":
            continue
        MOVIES.append(content["Name"])
    print(f'Local Media Libary Includes:\nMovies: {len(MOVIES)}\nTV SHOWS: {len(TV_SHOWS)}')
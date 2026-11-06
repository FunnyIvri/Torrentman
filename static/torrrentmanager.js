const torrents = document.getElementById("torrents")
const contextMenu = document.getElementById('torrentmanage-context-menu')
let parsedTorrentsData = null
function updateTorrentData() {
    fetch("/gettorrents").then((res) => {
        res.text().then((torrentsData) => {
            torrents.replaceChildren()
            parsedTorrentsData = JSON.parse(torrentsData)
            if (parsedTorrentsData.length <= 0) {
                let noTorrentsText = document.createElement("h1");
                noTorrentsText.textContent = "NO ACTIVE TORRENTS";
                torrents.appendChild(noTorrentsText);
            }
            parsedTorrentsData.forEach((torrent, index) => {
                let torrentContainer = document.createElement("div");
                torrentContainer.className = "torrent"
                let name = document.createElement('h1');
                name.textContent = torrent['name'];
                let progress = document.createElement('progress');
                progress.max = 100
                try {
                    progress.value = parseInt(torrent['progress']);
                }
                catch { }
                let information = document.createElement('h3');
                let captilizedTorrentState = torrent['state'][0].toUpperCase() + torrent['state'].slice(1);
                information.textContent = `${captilizedTorrentState} • ${torrent['progress']} • ${torrent["time_left"]}`;
                let dataAmount = document.createElement('h3');
                let gb_downloaded = torrent["total_download"] / (1024 ** 3)
                let gb_total = torrent["total_size"] / (1024 ** 3)
                dataAmount.textContent = `${gb_downloaded.toFixed(1)} GB/${gb_total.toFixed(1)} GB - ${torrent["speed"]}`

                torrentContainer.addEventListener("click", () => {
                    let doDelete = window.confirm("Delete Torrent?")
                    if (doDelete) {
                        const body = new URLSearchParams();
                        body.append("info_hash", torrent["info_hash"]);
                        fetch('/torrent/remove/', { method: 'POST', body: body })
                    }
                })


                torrentContainer.appendChild(name)
                torrentContainer.appendChild(progress)
                torrentContainer.appendChild(information)
                torrentContainer.appendChild(dataAmount)
                torrents.appendChild(torrentContainer)
            })
            setTimeout(updateTorrentData, 1000)
        })
    })
    
}
function createTh(text) {
    let th = document.createElement('th');
    th.textContent = text
    return th
}

updateTorrentData()
const resultsholder = document.getElementById("results")
//SETUP PAGE WITH SEARCH RESULTS
if (window.contentname) {
    loadsearchresults(window.contentname)
}
function searchfrominput() {
    const inputnode = document.getElementById("searchbox")
    resultsholder.replaceChildren();
    loadsearchresults(inputnode.value)
}
function loadsearchresults(query) {
    fetch(`/search/${query}`).then((res) => {
        res.text().then((text) => {
            data = JSON.parse(text);
            console.log(data["data"])
            for (const stream of data["data"]) {
                const resultholder = document.createElement("div");
                resultholder.className = "result";
                const icon = document.createElement('i')
                icon.classList.add("fa-solid", "fa-download")
                const nameText = document.createElement("h2");
                const nameLink = document.createElement('a');
                const downloadbutton = document.createElement("button");
                nameLink.href = stream["url"];
                nameLink.target = "_blank"
                nameText.textContent = `${stream["name"]}(${stream['size']})`;
                nameText.className = "name"
                downloadbutton.appendChild(icon)
                downloadbutton.className = "downloadbutton";
                downloadbutton.setAttribute("magnet", stream["magnet"])
                downloadbutton.setAttribute("piratelink", stream["url"])
                downloadbutton.setAttribute("title", stream["name"])
                if (stream['category'].toLocaleLowerCase().includes("movies")) {
                    downloadbutton.onclick = (e) => { sendDownloadRequestMovie(e) };
                }
                else {
                    downloadbutton.onclick = (e) => { sendDownloadRequestShow(e) };
                }
                const hr = document.createElement("hr")
                hr.className = "line"
                resultsholder.append(hr);
                nameLink.appendChild(nameText);
                resultholder.appendChild(nameLink);
                resultholder.appendChild(downloadbutton);
                resultsholder.appendChild(resultholder);

            }
        })
    })
}
async function sendDownloadRequestShow(e) {
    const target = e.currentTarget;
    let res = await fetch(`/getimdb/${target.getAttribute("piratelink")}`)
    let imdbId = await res.text()
    if (typeof (imdbId) != "string") {
        let movieName = extractMovieName(target.getAttribute("title"));
        let movieRes = await fetch(`/searchimdb/${movieName}`);
        let movieData = JSON.parse(await movieRes.text());

        imdbId = movieData.imdbID
        imdbId = imdbId.slice(2, imdbId.length)
        console.log(imdbId)
    }
    const episodeAndSeasonRegex = /[sS](\d{2})[eE](\d{2})/;
    const seasonRegex = /[sS]\d{2}/;
    const episodeAndSeasonMatch = target.getAttribute("title").match(episodeAndSeasonRegex);
    const seasonMatch = target.getAttribute("title").match(seasonRegex);
    let seasonAndEpisodePath = ''
    if (episodeAndSeasonMatch) {
        seasonAndEpisodePath = `${episodeAndSeasonMatch[0]}/${episodeAndSeasonMatch[1]}`
    }
    else if (seasonMatch) {

        seasonAndEpisodePath = seasonMatch[0].slice(1, seasonMatch[0].length)
    }
    const body = new URLSearchParams();
    body.append("magnet", target.getAttribute("magnet"));
    fetch(`/download/show/${imdbId}/${seasonAndEpisodePath}`, { method: 'POST', body: body }).catch((error) => { alert(error); return }).then((res) => {
        window.location.replace("/managetorrents");
    });
}

async function sendDownloadRequestMovie(e) {
    const target = e.currentTarget;
    let res = await fetch(`/getimdb/${target.getAttribute("piratelink")}`)
    let imdbId = await res.text()
    if (typeof (imdbId) != "string") {
        let movieName = extractMovieName(target.getAttribute("title"));
        let movieRes = await fetch(`/searchimdb/${movieName}`);
        let movieData = JSON.parse(await movieRes.text());

        imdbId = movieData.imdbID
        imdbId = imdbId.slice(2, imdbId.length)
    }
    alert(imdbId)
    const body = new URLSearchParams();
    body.append("magnet", target.getAttribute("magnet"));
    fetch(`/download/movie/${imdbId}/`, { method: 'POST', body: body }).catch((error) => { alert(error); return }).then(() => {
        window.location.replace("/managetorrents");
    });

}

function extractMovieName(name) {
    const match = name.match(/^(.+?)(?:[.\s]+)(?:\(\d{4}\)|\d{4})(?:[.\s\[]|$)/);

    if (!match) {
        return name.trim();
    }

    return match[1]
        .replace(/[._]+/g, " ")
        .trim();
}
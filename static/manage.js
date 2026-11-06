const constantsContainer = document.getElementById("constantsContainer");
async function loadConstants() {
    let res = await fetch('/constants/get');
    let constantsText = await res.text();
    for (let line of constantsText.split('\n')) {
        line = line.replace(' ', ''); //remove spaces
        line = line.split('=');
        let i = 0;

        let constantValue = '';
        for (let part of line) {
            i++
            if (i == 1) { continue; }
            if  (i >2){
                constantValue+="="
            }
            constantValue += part;

        }
        let constantName = line[0];
        let container = document.createElement('div')
        let label = document.createElement('label');
        let input = document.createElement('input');
        label.textContent = constantName + ": ";
        input.value = constantValue;
        input.id = constantName;
        label.htmlFor = constantName;
        container.appendChild(label);
        container.appendChild(input);
        constantsContainer.appendChild(container);
    }
}
function saveConstants() {
    let constantsString = ''
    for (let node of constantsContainer.children) {
        let input = node.children[1]
        let constantName = input.id;
        let constantValue = input.value;
        constantsString += `${constantName} = ${constantValue}\n`
    }
    const body = new URLSearchParams();
    body.append("constants", constantsString)
    fetch("/constants/set", { method: 'POST', body: body }).catch((e) => { alert(e) }).then((res) => { alert(res.statusText + " - restart torrentmanager to take effects") })
}


function runCommand(command){
    console.log(command)
    fetch(command,{method:'POST'}).catch((e) => { alert(e) }).then((res) => { alert(res.statusText);window.location.reload() })
    
}
loadConstants()

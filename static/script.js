function add_content(){
    const newContentName = prompt("Content Name");
    window.location.replace(`/add/${newContentName}`)
}
